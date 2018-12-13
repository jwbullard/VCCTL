/*
 * VcctlServletContextListener.java
 *
 * Created on September 12, 2005, 10:57 AM
 */

package nist.bfrl.vcctl.application;

import javax.servlet.ServletContextListener;
import javax.servlet.ServletContextEvent;

import nist.bfrl.vcctl.execute.RunningOperations;

/**
 *
 * @author  tahall
 * @version
 *
 * Web application lifecycle listener.
 */

public class VcctlServletContextListener implements ServletContextListener {
    /**
     * ### Method from ServletContextListener ###
     *
     * Called when a Web application is first ready to process requests
     * (i.e. on Web server startup and when a context is added or reloaded).
     *
     * For example, here might be database connections established
     * and added to the servlet context attributes.
     */
    public void contextInitialized(ServletContextEvent evt) {
        RunningOperations runops = RunningOperations.INSTANCE;
        
        if (!runops.isRunning()) {
            runops.start();
        }
    }
    
    /**
     * ### Method from ServletContextListener ###
     *
     * Called when a Web application is about to be shut down
     * (i.e. on Web server shutdown or when a context is removed or reloaded).
     * Request handling will be stopped before this method is called.
     *
     * For example, the database connections can be closed here.
     */
    public void contextDestroyed(ServletContextEvent evt) {
        RunningOperations runops = RunningOperations.INSTANCE;
        
        runops.stop();
    }
}
