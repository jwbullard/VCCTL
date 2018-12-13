/*
 * GenMic.java
 *
 * Created on August 19, 2005, 1:12 PM
 */

package nist.bfrl.vcctl.operation.microstructure.genmic;

import java.sql.SQLException;
import java.util.concurrent.*;
import java.io.*;
import java.io.IOException;
import java.lang.Throwable;

import nist.bfrl.vcctl.application.Vcctl;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.*;
import nist.bfrl.vcctl.operation.*;
import nist.bfrl.vcctl.operation.microstructure.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.execute.Cancellable;

/**
 *
 * @author tahall
 */
public class GenMic implements Callable<String>, Cancellable {
    
    private Operation op;
    private Process child;
    private boolean was_cancelled;
    
    /** Creates a new instance of GenMic */
    public GenMic(Operation op) {
        this.op = op;
        this.child = null;
        this.was_cancelled = false;
    }
    
    public String call() throws Exception {
        return execute_genmic();
    }
    
    public void cancel() {
        if (this.child != null) {
            this.child.destroy();
        }
        this.was_cancelled = true;
    }

    private String execute_genmic() throws SQLException, SQLArgumentException {
        // start the operation
        final String opname = op.getName();
        OperationDatabase.startOperationForUser(opname,op.getUsername());
        
        // Create command for genmic
        final String infile = opname + ".img.in";
        final String outfile = opname + ".img.out";
        final String dir = Vcctl.getBinDirectory();
        String command = dir + "genmic";
        
        final String userName = op.getUsername();
        // UserDirectory ud = UserDirectory.INSTANCE;
        UserDirectory userDir = new UserDirectory(userName);
        final String imgdir = userDir.getOperationDir(opname);
        
        

        // Create a child process to execute genmic
        ProcessBuilder pb = new ProcessBuilder(command);
        child = null;
        try {
            child = pb.start();
        } catch (IOException iox) {
            String detailedMessage = iox.getMessage();
            System.out.println("Exception: " + detailedMessage);
            System.out.flush();
            throw new RuntimeException(iox);
        }

        // Capture output from genmic
        final StringBuffer outtext = new StringBuffer("");
        Thread th = new Thread(new Runnable() {
            public void run() {
                InputStream in = null;
                in = child.getInputStream();
                try {
                    if (in != null) {
                        BufferedReader reader = new BufferedReader(new InputStreamReader(in));
                        String line = reader.readLine();
                        while ((line != null)) {
                            outtext.append(line).append("\n");
                            ServerFile.appendUserOpTextFile(userName, opname, outfile, line+"\n");
                            line = reader.readLine();
                        }
                    }
                } catch (IOException iox) {
                    System.out.println("GenMic caught IOException 2");
                    throw new RuntimeException(iox);
                }
            }
        });
        th.start();

        // Write input to genmic
        String intext = ServerFile.readUserOpTextFile(userName, opname, infile);
        OutputStream out = child.getOutputStream();
        try {
            out.write(intext.getBytes());
            out.close();
        } catch (IOException iox) {
            String detailedMessage = iox.getMessage();
            System.out.println("Exception: " + detailedMessage);
            System.out.flush();
            throw new RuntimeException(iox);
        }
        
        try {
          th.join();
        } catch (InterruptedException intx) {
            String detailedMessage = intx.getMessage();
            System.out.println("Exception: " + detailedMessage);
            System.out.flush();
        }

        //ServerFile.writeOpTextFile(opname, outfile, outtext.toString());
        
        // If microstructure image was successfully created, get the microstructure statistics
        String imgpath = userDir.getOperationFilePath(opname, opname + ".img");
        File imgfile = new File(imgpath);
        if (imgfile.exists()) {
            String statpath = imgpath.substring(0, imgpath.length()-4);
            statpath += ".stt";
            command = dir+"stat3d";
            pb = new ProcessBuilder(command);
            try {
                child = pb.start();
            } catch (IOException iox) {
                throw new RuntimeException(iox);
            }
            out = child.getOutputStream();
            intext = imgpath + "\n" + statpath + "\n";
            try {
                out.write(intext.getBytes());
                out.close();
            } catch (IOException iox) {
                
            }
        }
        if (!this.was_cancelled) {
            OperationDatabase.saveFinishedOperationForUser(opname,userName);
        }
        
        return outtext.toString();
    }
}
