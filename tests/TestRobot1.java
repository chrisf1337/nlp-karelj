// -*- mode: java; -*-

import kareltherobot.*;
import static kareltherobot.Directions.*;
import java.nio.file.*;
import java.lang.reflect.*;
import java.io.*;
import java.lang.*;

public class TestRobot1 {
    public static void main(String args[]) {
        UrRobot karel = new UrRobot(2, 2, East, 0);
        String result = "";
        // this will get all fields declared by the input class
        Field locField = null;
        Field dirField = null;
        try {
            locField = karel.getClass().getDeclaredField("loc");
            dirField = karel.getClass().getDeclaredField("direction");
        } catch (NoSuchFieldException e) {
            System.out.println(e.getMessage());
            System.exit(1);
        }
        locField.setAccessible(true);
        dirField.setAccessible(true);

        // ===== Begin injected code =====
        karel.turnLeft();
        karel.move();
        karel.turnLeft();
        karel.turnLeft();
        karel.turnLeft();
        karel.turnLeft();
        karel.turnLeft();
        karel.turnLeft();
        karel.move();
        // ===== End injected code =====

        karel.showState("");
        World.saveWorld("end-1-test.kwld");
        int[] loc = {0, 0, 0, 0};
        Direction dir = null;
        try {
            loc = (int [])locField.get(karel);
            dir = (Direction)dirField.get(karel);
        } catch (IllegalAccessException e) {
            System.out.println(e.getMessage());
            System.exit(1);
        }
        // System.out.format("%d %d %d %d\n", loc[0], loc[1], loc[2], loc[3]);
        // System.out.format("%s\n", dir);
        try {
            Files.write(Paths.get("end-1-test.kwld"),
                String.format("robot %d %d %s", loc[0], loc[3], dir).getBytes(),
                StandardOpenOption.APPEND);
        } catch (IOException e) {
            System.out.println(e.getMessage());
            System.exit(1);
        }
    }

    static {
        World.reset();
        World.readWorld("start-1.kwld");
        World.setDelay(0);
        World.setVisible(false);
    }
}
