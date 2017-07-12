/*
* Argus Open Source
* Software to apply Statistical Disclosure Control techniques
* 
* Copyright 2014 Statistics Netherlands
* 
* This program is free software; you can redistribute it and/or 
* modify it under the terms of the European Union Public Licence 
* (EUPL) version 1.1, as published by the European Commission.
* 
* You can find the text of the EUPL v1.1 on
* https://joinup.ec.europa.eu/software/page/eupl/licence-eupl
* 
* This software is distributed on an "AS IS" basis without 
* warranties or conditions of any kind, either express or implied.
*/

package tauargus.utils;

import argus.utils.SystemUtils;
import static argus.utils.SystemUtils.getApplicationDirectory;
import java.io.BufferedReader;
//import java.io.BufferedWriter;
import java.io.File;
//import java.io.FileFilter;
//import java.io.FileNotFoundException;
//import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
//import java.lang.reflect.InvocationTargetException;
//import java.net.URI;
//import java.net.URISyntaxException;
//import java.net.URL;
//import java.text.DecimalFormat;
//import java.text.DecimalFormatSymbols;
//import java.text.SimpleDateFormat;
//import java.util.Calendar;
import java.util.List;
//import java.util.logging.Level;
//import java.util.logging.Logger;
//import java.util.prefs.Preferences;
//import org.apache.commons.io.FilenameUtils;
//import org.apache.commons.io.filefilter.WildcardFileFilter;
//import tauargus.gui.DialogOpenMicrodata;
import tauargus.gui.FrameInfo;
//import tauargus.gui.FrameMain;
//import tauargus.gui.PanelTable;
import tauargus.model.Application;
//import java.awt.*;
//import java.awt.event.*;
//import javax.swing.*;
//import tauargus.gui.DialogInfo;

// Only the exec routines are left
// The rest is to the Argus lib SystemUtils

public class ExecUtils {
//    private static String logbook;
    
 
   static FrameInfo windowInfo;
//    static DialogInfo windowInfo;
   
       
    private static void eatStream(final InputStream is, final Boolean silent) {
        Thread thread;  
        thread = new Thread() {
            @Override
            public void run() {
                String line; //Anco
// Anco 1.6         
//         try (BufferedReader reader = new BufferedReader(new InputStreamReader(is))) {
                BufferedReader reader = null;
                try {
                    reader = new BufferedReader(new InputStreamReader(is));
//                    while (reader.readLine() != null) { versie Robert
//                    }
                    while ((line = reader.readLine()) != null) { //Anco
                        System.out.println(line); //Anco
                        if (!silent) windowInfo.addText(line);
                    }
                } 
                catch (IOException ex) {}
            }
        };
        thread.start();
    }
        
    /**
     * Finds the location of a given class file on the file system. Throws an
     * IOException if the class cannot be found.
     * <br>
     * If the class is in an archive (JAR, ZIP), then the returned object will
     * point to the archive file.
     * <br>
     * If the class is in a directory, the base directory will be returned with
     * the package directory removed.
     * <br>
     * The
     * <code>File.isDirectory()</code> method can be used to determine which is
     * the case.
     * <br>
     *
     * @author McDowell
     * @param c a given class
     * @return a File object
     * @throws IOException
     */

/*    To ArgisLib
    public static File getApplicationDirectory() throws IOException, FileNotFoundException {
        Class c = ExecUtils.class;
        if (c == null) {
            throw new NullPointerException();
        }

        String className = c.getName();
        String resourceName = className.replace('.', '/') + ".class";
        ClassLoader classLoader = c.getClassLoader();
        if (classLoader == null) {
            classLoader = ClassLoader.getSystemClassLoader();
        }
        URL url = classLoader.getResource(resourceName);

        String szUrl = url.toString();
        if (szUrl.startsWith("jar:file:")) {
            try {
                szUrl = szUrl.substring("jar:".length(), szUrl.lastIndexOf("!"));
                String path = FilenameUtils.getFullPath(szUrl);
                URI uri = new URI(path);
                return new File(uri);
            } catch (URISyntaxException e) {
                throw new IOException(e.toString());
            }
        } else if (szUrl.startsWith("file:")) {
            try {
                szUrl = szUrl.substring(0, szUrl.length() - resourceName.length());
                URI uri = new URI(szUrl);
                File file = new File(uri);
                // strip local build path (currently build/classes)
                return new File(uri).getParentFile().getParentFile();
            } catch (URISyntaxException e) {
                throw new IOException(e.toString());
            }
        }

        throw new FileNotFoundException(szUrl);
    }
*/
    
    /**
     * Start synchronously an external command. Output will be discarded.
     * 
     * @param commandString command to be executed.
     * @param workingDir working directory to be set for the process being called.
     * @param silent boolean, false: display progress-window, true: do not display progress-window
     */
    public static int execCommand(String commandString, String workingDir, Boolean silent, String header) {

        if (!silent){
          windowInfo = new FrameInfo();    
//        windowInfo = new DialogInfo(FrameMain, false);
          windowInfo.setVisible(true);
//        windowInfo.requestFocusInWindow();
//        windowInfo.setAlwaysOnTop(true);
          windowInfo.addLabel (header); 
          
        }
//        frameInfo.repaint();
//        frameInfo.validate();

        try {
            Process process;
            ProcessBuilder pb;
            if (workingDir == null) {
                //process = Runtime.getRuntime().exec(commandString);
                pb = new ProcessBuilder(commandString);
                pb.environment().put("LD_LIBRARY_PATH", getApplicationDirectory(Application.class).getCanonicalPath());
                process = pb.start();
            } else {
                //process = Runtime.getRuntime().exec(commandString, null, new File(workingDir));
                pb = new ProcessBuilder(commandString);
                pb.environment().put("LD_LIBRARY_PATH", getApplicationDirectory(Application.class).getCanonicalPath());
                pb.directory(new File(workingDir));
                process = pb.start();
            }
            eatStream(process.getInputStream(),silent);
            eatStream(process.getErrorStream(),silent);
            int exitCode = process.waitFor();
            //windowInfo.setVisible(false);
            if (exitCode != 0) {
                System.out.println("Process terminated with exit code " + exitCode);
            } else {
                System.out.println("Process terminated succesfully." + exitCode);
            }
            return exitCode;
        } catch (IOException ex) {
            //windowInfo.setVisible(false);
            System.out.println("Unable to start: " + commandString);
        } catch (InterruptedException ex) {
            //windowInfo.setVisible(false);
            System.out.println("Process is interrupted: " + commandString);
        } finally {
            if (!silent) windowInfo.setVisible(false);
        }
        return -99;
    }
    
    /**
     * Start synchronously an external command. Output will be discarded.
     * 
     * @param commandString command to be executed.
     */
    public static int execCommand(String commandString) {
        return execCommand(commandString, null, true, "");
    }

    /**
     * Start synchronously an external command. Output will be discarded.
     * 
     * @param commandString list with command to be executed and additional options.
     * @param workingDir working directory to be set for the process being called.
     * @param silent boolean, false: display progress-window, true: do not display progress-window
     */
    public static int execCommand(List<String> commandString, String workingDir, Boolean silent, String header) {
        String hs;
        if (!silent){
          windowInfo = new FrameInfo();    
//        windowInfo = new DialogInfo(FrameMain, false);
          windowInfo.setVisible(true);
//        windowInfo.requestFocusInWindow();
//        windowInfo.setAlwaysOnTop(true);
          windowInfo.addLabel (header); 
          
        }
// remove the .exe extension if not windows        
        if (!SystemUtils.isWindows()){
          hs = commandString.get(0);
          if (hs.toUpperCase().endsWith(".EXE")){hs = hs.substring(0,hs.length()-4);}
          commandString.set(0,hs);
        }
//        frameInfo.repaint();
//        frameInfo.validate();

        try {
            Process process;
            ProcessBuilder pb;
            if (workingDir == null) {
                //process = Runtime.getRuntime().exec(commandString);
                pb = new ProcessBuilder(commandString);
                pb.environment().put("LD_LIBRARY_PATH", getApplicationDirectory(Application.class).getCanonicalPath());
                process = pb.start();
            } else {
                //process = Runtime.getRuntime().exec(commandString, null, new File(workingDir));
                pb = new ProcessBuilder(commandString);
                pb.environment().put("LD_LIBRARY_PATH", getApplicationDirectory(Application.class).getCanonicalPath());
                pb.directory(new File(workingDir));
                process = pb.start();
            }
            eatStream(process.getInputStream(),silent);
            eatStream(process.getErrorStream(),silent);
            int exitCode = process.waitFor();
            //windowInfo.setVisible(false);
            if (exitCode != 0) {
                System.out.println("Process terminated with exit code " + exitCode);
            } else {
                System.out.println("Process terminated succesfully." + exitCode);
            }
            return exitCode;
        } catch (IOException ex) {
            //windowInfo.setVisible(false);
            System.out.println("Unable to start: " + commandString);
        } catch (InterruptedException ex) {
            //windowInfo.setVisible(false);
            System.out.println("Process is interrupted: " + commandString);
        } finally {
            if (!silent) windowInfo.setVisible(false);
        }
        return -99;
    }
 
    
/*    To ArgisLib
    public static String now() {
        final String DATE_FORMAT_NOW = "dd-MMM-yyyy HH:mm:ss";
        Calendar cal = Calendar.getInstance();
        SimpleDateFormat sdf = new SimpleDateFormat(DATE_FORMAT_NOW);
        return sdf.format(cal.getTime());
    }
    
    public static void writeLogbook (String message){
        String hs; int p;
        if (message.equals("")){hs="";}
        else {hs = now() + " : "+ message;}
          try{
          BufferedWriter out = new BufferedWriter(new FileWriter(logbook, true));
          while (!hs.equals("")){
            p = hs.indexOf("\n");
            if (!(p == -1)){
                out.write (hs.substring(0,p)); out.newLine();
                hs = "                       "+hs.substring(p+1);
            } else {   
             out.write(hs); out.newLine(); hs = "";
            }
          }
          out.close();        
          
          } catch(IOException ex){}          
    }
    
    public static void setLogbook (String lb){
        logbook = lb;
    }
    
    public static File[] getFiles(String filePattern) {
        String dirPath = FilenameUtils.getFullPath(filePattern);
        String pattern = FilenameUtils.getName(filePattern);
        File dir = new File(dirPath);
        FileFilter fileFilter = new WildcardFileFilter(pattern);
        return dir.listFiles(fileFilter);
    }
    
    public static boolean isWindows() {
        String OS = System.getProperty("os.name").toLowerCase();
        return OS.indexOf("win") >= 0;
    }
    
    private static String getInternationalValue(String key, String defaultValue) throws IllegalArgumentException, IllegalAccessException, InvocationTargetException {
        return WinRegistry.readString(WinRegistry.HKEY_CURRENT_USER, "Control Panel\\International", key);
    }

    public static DecimalFormat getSystemDecimalFormat() {
        DecimalFormat decimalFormat = new DecimalFormat();
        if (isWindows()) {
            DecimalFormatSymbols decimalFormatSymbols = decimalFormat.getDecimalFormatSymbols();
            try {
                char decimalSymbol = getInternationalValue("sDecimal", ".").charAt(0);
                char thousandSymbol = getInternationalValue("sThousand", ",").charAt(0);
                decimalFormatSymbols.setDecimalSeparator(decimalSymbol);
                decimalFormatSymbols.setGroupingSeparator(thousandSymbol);
                decimalFormat.setDecimalFormatSymbols(decimalFormatSymbols);
// Anco 1.6                
//            } catch (IllegalArgumentException | IllegalAccessException | InvocationTargetException ex) {
            } catch (IllegalArgumentException ex) {
                Logger.getLogger(ExecUtils.class.getName()).log(Level.SEVERE, null, ex);}
              catch (IllegalAccessException ex) {
                Logger.getLogger(ExecUtils.class.getName()).log(Level.SEVERE, null, ex);}
              catch (InvocationTargetException ex) {
                Logger.getLogger(ExecUtils.class.getName()).log(Level.SEVERE, null, ex);
            }
        }
        return decimalFormat;
    }
    
    public static DecimalFormat getInternalDecimalFormat(int fractionDigits) {
        DecimalFormat decimalFormat = new DecimalFormat();
        DecimalFormatSymbols decimalFormatSymbols = decimalFormat.getDecimalFormatSymbols();
        decimalFormatSymbols.setDecimalSeparator('.');
        decimalFormatSymbols.setGroupingSeparator(',');
        decimalFormat.setDecimalFormatSymbols(decimalFormatSymbols);
        decimalFormat.setGroupingUsed(false);
        decimalFormat.setMinimumFractionDigits(fractionDigits);
        decimalFormat.setMaximumFractionDigits(fractionDigits);
        return decimalFormat;
    }
*/    
    public static void main(String[] args) {
//        try {
            // execCommand("c:\\Program Files\\Microsoft Office\\Office14\\WINWORD.EXE c:\\Users\\Gebruiker\\Projects\\TauArgus\\doc\\Install.docx", "c:\\Users\\Gebruiker\\Google Drive\\TauJava");
//            System.out.println(getApplicationDirectory().getCanonicalPath());
//        } catch (FileNotFoundException ex) {
//            Logger.getLogger(ExecUtils.class.getName()).log(Level.SEVERE, null, ex);
//        } catch (IOException ex) {
//            Logger.getLogger(ExecUtils.class.getName()).log(Level.SEVERE, null, ex);
//        }
    }
/*    
    public static void putRegBoolean(String subRoot, String name, Boolean boolKey){
        Preferences p = Preferences.userRoot().node("tauargus/"+subRoot);
//        Preferences p = Preferences.userNodeForPackage(Application.class);
        p.putBoolean(name, boolKey);
//        Application.anco = p.getBoolean("anco", false);
    }
    
    public static void removeRegKey(String subRoot, String name){
       Preferences p = Preferences.userRoot().node("tauargus/"+subRoot);
       p.remove(name);
    }
    

    public static boolean getRegBoolean(String subRoot, String name, boolean defaultkey){
        boolean b = defaultkey;
        Preferences p = Preferences.userRoot().node("tauargus/"+subRoot);
//        Preferences p = Preferences.userNodeForPackage(Application.class);
        b = p.getBoolean(name, b);
//        Application.anco = p.getBoolean("anco", false);
        return b;
    }

      public static void putRegInteger(String subRoot, String name, Integer intKey){
        Preferences p = Preferences.userRoot().node("tauargus/"+subRoot);
//        Preferences p = Preferences.userNodeForPackage(Application.class);
        p.putInt(name, intKey);
//        Application.anco = p.getBoolean("anco", false);
    }
    

    public static Integer getRegInteger(String subRoot, String name, Integer defaultkey){
        Integer i = defaultkey;
        Preferences p = Preferences.userRoot().node("tauargus/"+subRoot);
//        Preferences p = Preferences.userNodeForPackage(Application.class);
        i = p.getInt(name, i);
//        Application.anco = p.getBoolean("anco", false);
        return i;
    }
  
      public static void putRegDouble(String subRoot, String name, Double doubleKey){
        Preferences p = Preferences.userRoot().node("tauargus/"+subRoot);
//        Preferences p = Preferences.userNodeForPackage(Application.class);
        p.putDouble(name, doubleKey);
//        Application.anco = p.getBoolean("anco", false);
    }
    

    public static Double getRegDouble(String subRoot, String name, Double defaultkey){
        Double d = defaultkey;
        Preferences p = Preferences.userRoot().node("tauargus/"+subRoot);
//        Preferences p = Preferences.userNodeForPackage(Application.class);
        d = p.getDouble(name, d);
//        Application.anco = p.getBoolean("anco", false);
        return d;
    }    
      public static void putRegString(String subRoot, String name, String strKey){
        Preferences p = Preferences.userRoot().node("tauargus/"+subRoot);
//        Preferences p = Preferences.userNodeForPackage(Application.class);
        p.put(name, strKey);
//        Application.anco = p.getBoolean("anco", false);
    }
    

    public static String getRegString(String subRoot, String name, String defaultkey){
        String s = defaultkey;
        Preferences p = Preferences.userRoot().node("tauargus/"+subRoot);
//        Preferences p = Preferences.userNodeForPackage(Application.class);
        s = p.get(name, s);
//        Application.anco = p.getBoolean("anco", false);
        return s;
    }
*/
    
}
