/*
 * HydMic.java
 *
 * Created on October 12, 2005, 2:08 PM
 *
 * To change this template, choose Tools | Options and locate the template under
 * the Source Creation and Management node. Right-click the template and choose
 * Open. You can then make changes to the template in the Source Editor.
 */

package nist.bfrl.vcctl.operation.hydration;

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
 * @author tahall
 */
public class HydMic implements Callable<String>, Cancellable {
    
    private Process child;
    private boolean was_cancelled;
    
    private Operation op;
    
    /** Creates a new instance of HydMic */
    public HydMic(Operation op) {
        this.op = op;
        this.child = null;
        this.was_cancelled = false;
    }
    
    public String call() throws Exception {
        return execute_hydmic();
    }
    
    public void cancel() {
        if (this.child != null) {
            this.child.destroy();
        }
        this.was_cancelled = true;
    }
    
    private String execute_hydmic() throws SQLException, SQLArgumentException {
        // start the operation
        String opname = op.getName();
        OperationDatabase.startOperationForUser(opname,op.getUsername());
        
        String userName = op.getUsername();
        
        // Create command for hydmic
        String infile = opname + ".hyd.in";
        String outfile = opname + ".hyd.out";
        String dir = Vcctl.getBinDirectory();
        String command = dir + "disrealnew";
        
        String intext = ServerFile.readUserOpTextFile(userName, opname, infile);
        
        ProcessBuilder pb = new ProcessBuilder(command);
        String opdir = ServerFile.getUserOperationDir(userName, opname);
        pb.directory(new File(opdir));
        
        // Write input to hydmic
        child = null;
        try {
            child = pb.start();
            OutputStream out = child.getOutputStream();
            out.write(intext.getBytes());
            out.close();
        } catch (IOException iox) {
            
        }
        
        // Capture hydmic output
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
