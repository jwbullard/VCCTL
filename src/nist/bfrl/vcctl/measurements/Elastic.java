/*
 * Elastic.java
 *
 * Created on May 31, 2006, 10:32 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.measurements;

import java.sql.SQLException;
import java.util.concurrent.*;
import java.io.*;

import nist.bfrl.vcctl.application.Vcctl;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.*;
import nist.bfrl.vcctl.operation.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.execute.Cancellable;

/**
 *
 * @author tahall
 */
public class Elastic implements Callable<String>, Cancellable {
    
    private Process child;
    private boolean was_cancelled;
    private Operation op;
    
    /**
     * Creates a new instance of Elastic
     */
    public Elastic(Operation op) {
        this.op = op;
        this.child = null;
        this.was_cancelled = false;
    }
    
    public String call() throws Exception {
        return execute_elastic();
    }
    
    public void cancel() {
        if (this.child != null) {
            this.child.destroy();
        }
        this.was_cancelled = true;
    }
    
    private String execute_elastic() throws SQLException, SQLArgumentException {
        // start the operation
        String opname = op.getName();
        OperationDatabase.startOperationForUser(opname,op.getUsername());
        
        // Create command for elastic
        String infile = "elastic.in";
        String outfile = "elastic.out";
        String dir = Vcctl.getBinDirectory();
        String command = dir + "elastic";
        
        String userName = op.getUsername();
        String intext = ServerFile.readUserOpTextFile(userName, opname, infile);
        
        ProcessBuilder pb = new ProcessBuilder(command);
        String opdir = ServerFile.getUserOperationDir(userName, opname);
        pb.directory(new File(opdir));
        
        // Write input to executable
        child = null;
        try {
            child = pb.start();
            OutputStream out = child.getOutputStream();
            out.write(intext.getBytes());
            out.close();
        } catch (IOException iox) {
            
        }
        
        // Capture elastic output
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
            // Do nothing
        }
        
        if (!this.was_cancelled) {
            OperationDatabase.saveFinishedOperationForUser(opname,op.getUsername());
        }
        
        return outtext.toString();
    }
}
