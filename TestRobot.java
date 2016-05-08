// -*- mode: java; -*-

import kareltherobot.*;
import static kareltherobot.Directions.*;
import java.nio.file.*;
import java.lang.reflect.*;
import java.io.*;
import java.lang.*;

public class TestRobot {
    public static void main(String args[]) {
        UrRobot karel = new UrRobot(2, 2, East, 0);
        String result = "";
        // this will get all fields declared by the input class
        Field locField = null;
        try {
            locField = karel.getClass().getDeclaredField("loc");
        } catch (NoSuchFieldException e) {
            System.out.println(e.getMessage());
            System.exit(1);
        }
        locField.setAccessible(true);
        int[] loc = {0, 0, 0, 0};
        try {
            loc = (int [])locField.get(karel);
        } catch (IllegalAccessException e) {
            System.out.println(e.getMessage());
            System.exit(1);
        }
        karel.turnLeft();
        karel.move();
        karel.move();
        karel.move();
        karel.showState("");
        World.saveWorld("end-1-test.kwld");
        try {
            Files.write(Paths.get("end-1-test.kwld"),
                String.format("robot %d %d", loc[0], loc[2]).getBytes(),
                StandardOpenOption.APPEND);
        } catch (IOException e) {
            System.out.println(e.getMessage());
            System.exit(1);
        }
    }

    static {
        World.reset();
        World.readWorld("start-1.kwld");
        World.setDelay(50);
        World.setVisible(true);
    }
}
