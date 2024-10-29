/*
 * Concelas.java
 *
 * Created on June 5, 2007, 10:52 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.operation.microstructure.concelas;

import java.util.concurrent.*;
import java.io.*;

import nist.bfrl.vcctl.application.Vcctl;
import nist.bfrl.vcctl.util.*;
import nist.bfrl.vcctl.operation.*;
import nist.bfrl.vcctl.operation.microstructure.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.execute.Cancellable;

/**
 *
 * @author Mathieu Scialom
 */
public class Concelas implements Callable<String>, Cancellable {
    
    private Operation op;
    private Process child;
    private boolean was_cancelled;
    
    /**
     * Creates a new instance of Concelas
     */
    public Concelas(Operation op) {
        this.op = op;
        this.child = null;
        this.was_cancelled = false;
    }
    
    public String call() throws Exception {
        return execute_concelas();
    }
    
    public void cancel() {
        if (this.child != null) {
            this.child.destroy();
        }
        this.was_cancelled = true;
    }
    
    private String execute_concelas() {
        return "";
    }
}
