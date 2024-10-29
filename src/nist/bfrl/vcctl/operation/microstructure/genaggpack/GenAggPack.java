/*
 * GenAggPack.java
 *
 * Created on May 23, 2007, 11:04 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.operation.microstructure.genaggpack;

import java.sql.SQLException;
import java.util.concurrent.*;
import java.io.*;

import nist.bfrl.vcctl.application.Vcctl;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.*;
import nist.bfrl.vcctl.operation.*;
import nist.bfrl.vcctl.operation.microstructure.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.execute.Cancellable;

/**
 *
 * @author Mathieu Scialom
 */
public class GenAggPack implements Callable<String>, Cancellable {
    
    private Operation op;
    private Process child;
    private boolean was_cancelled;
    
    /** Creates a new instance of GenAggPack */
    public GenAggPack(Operation op) {
        this.op = op;
        this.child = null;
        this.was_cancelled = false;
    }
    
    public String call() throws Exception {
        return execute_genaggpack();
    }
    
    public void cancel() {
        if (this.child != null) {
            this.child.destroy();
        }
        this.was_cancelled = true;
    }
    
    private String execute_genaggpack() throws SQLException, SQLArgumentException {
        // start the operation
        String opname = op.getName();
        OperationDatabase.startOperationForUser(opname,op.getUsername());
        
        // Create command for genaggpack
        String infile = Constants.GENAGGPACK_INPUT_FILE;
        String outfile = Constants.GENAGGPACK_OUTPUT_FILE;
        String dir = Vcctl.getBinDirectory();
        String command = dir + "genaggpack";
        
        String userName = op.getUsername();
        // UserDirectory ud = UserDirectory.INSTANCE;
        UserDirectory userDir = new UserDirectory(userName);
        String imgdir = userDir.getOperationDir(opname);
        
        String intext = ServerFile.readUserOpTextFile(userName, opname, infile);
        // Create a child process to execute genaggpack
        ProcessBuilder pb = new ProcessBuilder(command);
        child = null;
        try {
            child = pb.start();
        } catch (IOException iox) {
            throw new RuntimeException(iox);
        }
        
        // Write input to genaggpack
        OutputStream out = child.getOutputStream();
        try {
            out.write(intext.getBytes());
            out.close();
        } catch (IOException iox) {
            
        }
        
        // Capture genaggpack output
        InputStream in = child.getInputStream();
        StringBuffer outtext = new StringBuffer("");
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
            throw new RuntimeException(iox);
        }
        
        //ServerFile.writeOpTextFile(opname, outfile, outtext.toString());
        
        // If microstructure image was successfully created, get the microstructure statistics
        /*
        String imgpath = ud.getOperationFilePath(opname, "Genaggpack files");
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
         **/
        if (!this.was_cancelled) {
            OperationDatabase.saveFinishedOperationForUser(opname,userName);
        }
        
        return outtext.toString();
    }
}
