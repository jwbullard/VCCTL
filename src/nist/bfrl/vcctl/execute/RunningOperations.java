/*
 * RunningOperations.java
 *
 * Created on September 8, 2005, 3:28 PM
 */

package nist.bfrl.vcctl.execute;

import java.io.*;
import java.net.*;
import java.sql.SQLException;

import javax.servlet.*;
import javax.servlet.http.*;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;

import java.util.*;
import java.util.concurrent.*;

import nist.bfrl.vcctl.database.*;

/**
 *
 * @author tahall
 * @version
 */
public class RunningOperations implements Runnable {
    
    static public RunningOperations INSTANCE = new RunningOperations();
    
    private Map<String, Cancellable> fm;
    protected RunningOperations() {
        running_ops = null;
        fm = new HashMap<String, Cancellable>();
    }
    
    private int max_running = Constants.MAXIMUM_RUNNING_OPERATIONS;
    
    public int getMax_running() {
        return max_running;
    }
    
    public void setMax_running(int max) {
        if (max > 0) {
            max_running = max;
        }
    }
    
    public boolean noPendingDependencies(Operation op) {
        String dependencies = op.getDepends_on_operation_name();
        
        if (dependencies.length() < 1) {
            return true;
        }
        
        return false;
    }
    
    private volatile Thread running_ops = null;
    public void stop() {
        running_ops = null;
    }
    
    public void start() {
        running_ops = new Thread(this);
        running_ops.setPriority(Thread.MIN_PRIORITY);
        running_ops.start();
    }
    
    public synchronized boolean isRunning() {
        if (running_ops == null) {
            return false;
        } else {
            return running_ops.isAlive();
        }
    }
    
    /**
     * Loop continuously as long as vcctl is running on Tomcat or other Java
     * server.  Every 5 seconds,
     */
    public void run() {
        int loop_count = 0;
        Thread thisThread = Thread.currentThread();
        while(running_ops == thisThread) {
            List<String> userNames;
            try {
                userNames = UserDatabase.getUserNames();
                String userName;
                for (int j = 0; j < userNames.size(); j++) {
                    userName = userNames.get(j);
                    // Get the count of currently running operations
                    List lrun = OperationDatabase.getOperationsByStatusForUser(Constants.OPERATION_RUNNING_STATUS, "start", userName);
                    if (lrun.size() < getMax_running()) {
                        // Are there any queued and waiting?
                        List lqueue = OperationDatabase.getOperationsByStatusForUser(Constants.OPERATION_QUEUED_STATUS, "queue", userName);
                        int queuelength = lqueue.size();
                        if (queuelength > 0) {
                            // Find first Operation waiting to be queued that has no dependencies or of which the dependencies are finished
                            // that are not finished and run it
                            boolean found_op = false;
                            for (int i=queuelength-1; i>=0 && !found_op; i--) {
                                Operation op = (Operation)lqueue.get(i);
                                
                                String dependencies = op.getDepends_on_operation_name();
                                String status = null;
                                if (dependencies != null && !dependencies.equalsIgnoreCase("")) {
                                    status = OperationDatabase.getOperationStatusForUser(dependencies,userName);
                                }
                                
                                if ((dependencies.length() < 1) || (status != null && status.equalsIgnoreCase(Constants.OPERATION_FINISHED_STATUS))) {
                                    // Start this operation
                                    Cancellable co = VcctlOperationExecutive.start(op);
                                    String key = userName + "." + op.getName(); // concatened key compound of the user name . the operation name
                                    fm.put(key, co);
                                    
                                    found_op = true;
                                } else if (OperationDatabase.getOperationForUser(dependencies,userName) == null) { // if the operation on which it depends doesn't exist, we can remove the current operation
                                    OperationDatabase.deleteOperationForUser(op.getName(),userName);
                                }
                            }
                        }
                        
                        /**
                         * Stop processes for operations marked 'cancelled' by the user
                         *
                         */
                        List lcancel = OperationDatabase.getOperationsByStatusForUser(Constants.OPERATION_CANCELLED_STATUS, "queue", userName);
                        for (int i=0; i<lcancel.size(); i++) {
                            Operation opc = (Operation)lcancel.get(i);
                            String key = userName + "." + opc.getName(); // concatened key compound of the user name . the operation name
                            Cancellable co = (Cancellable)fm.get(key);
                            if (co != null) {
                                co.cancel();
                            }
                        }
                    }
                    
                    // wait five seconds before processing queue
                    try {
                        running_ops.sleep(5000);
                    } catch (InterruptedException ignored) {
                        
                    }
                    
                    loop_count++;
                    
                    // Every twelve loops (one minute), check for crashed programs and
                    // other errors
                    if (loop_count == 12) {
                        loop_count = 0;
                        // Check for crashed programs and other errors
                        Set<String> keys = fm.keySet();
                    }
                }
            } catch (SQLException ex) {
                ex.printStackTrace();
            } catch (SQLArgumentException ex) {
                ex.printStackTrace();
            }
        }
    }
    
    /*
    public void launchOperationNow(Operation op) {
        // Get the count of currently running operations
        List lrun = OperationDatabase.getOperationsByStatus(Constants.OPERATION_RUNNING_STATUS, "start");
        if (lrun.size() < getMax_running()) {
            String dependencies = op.getDepends_on_operation_name();
            if (dependencies.length() < 1) {
                // Start this operation
                Cancellable co = VcctlOperationExecutive.start(op);
                String opname = op.getName();
                fm.put(opname, co);
            }
        }
    }
     **/
}
