/*
 * VcctlHttpSessionListener.java
 *
 * Created on December 15, 2005, 4:58 PM
 */

package nist.bfrl.vcctl.application;

import javax.servlet.http.HttpSessionListener;
import javax.servlet.http.HttpSessionEvent;

import nist.bfrl.vcctl.execute.RunningOperations;

/**
 *
 * @author  tahall
 * @version
 *
 * Web application lifecycle listener.
 */

public class VcctlHttpSessionListener implements HttpSessionListener {
    /**
     * ### Method from HttpSessionListener ###
     * 
     * Called when a session is created.
     */
    public void sessionCreated(HttpSessionEvent evt) {
        RunningOperations runops = RunningOperations.INSTANCE;
        
        if (!runops.isRunning()) {
            runops.start();
        }
    }

    /**
     * ### Method from HttpSessionListener ###
     * 
     * Called when a session is destroyed(invalidated).
     */
    public void sessionDestroyed(HttpSessionEvent evt) {
        
    }
}
