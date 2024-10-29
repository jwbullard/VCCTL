/*
 * OperationDatabaseBean.java
 *
 * Created on July 19, 2005, 10:18 AM
 */

package nist.bfrl.vcctl.database;

import java.beans.*;
import java.io.Serializable;
import java.util.*;

/**
 * @author tahall
 */
public class OperationDatabaseBean extends Object implements Serializable {

    /**
     * Holds value of property hydration_profile_count.
     */
    private int hydration_profile_count;

    /**
     * Holds value of property hydration_profiles.
     */
    private Collection hydration_profiles;
    
    public OperationDatabaseBean() {

    }

    /**
     * Getter for property psd_sample_operations.
     * @return Value of property psd_sample_operations.
     */
    /*
    public Collection getPsd_sample_operations() {

        List l = OperationDatabase.finishedOperationsOfType("psd sample");
        
        return l;
    }
     **/

    /**
     * Getter for property finished_ microstructure_operations.
     * @return Value of property finished_microstructure_operations.
     */
    /*
    public Collection getFinished_microstructure_operations() {
        return OperationDatabase.finishedOperationsOfType(Constants.MICROSTUCTURE_OPERATION_TYPE);
    }
     **/

    /**
     * Getter for property microstructure_operation_count.
     * @return Value of property microstructure_operation_count.
     */
    /*
    public int getMicrostructure_operation_count() {

        int count = OperationDatabase.microstructure_operation_count();
        
        return count;
    }
     **/

    /**
     * Getter for property hydration_profile_count.
     * @return Value of property hydration_profile_count.
     */
    /*
    public int getHydration_profile_count() throws SQLException {

        return getHydration_profiles().size();
    }
     **/

    /**
     * Getter for property hydration_profiles.
     * @return Value of property hydration_profiles.
     */
    /*
    public Collection getHydration_profiles() throws SQLException {

        List l = OperationDatabase.profile_names();
        
        return l;
    }
     **/
    
    /*
    public Collection getHydrated_microstructures() {
        List l = OperationDatabase.hydratedMicrostructures();
        
        return l;
    }*/

    /**
     * Getter for property finished_running_or_queued_microstructure_operations.
     * @return Value of property finished_running_or_queued_microstructure_operations.
     */
    /*
    public Collection getFinished_running_or_queued_microstructure_operations() {
        return OperationDatabase.finishedRunningOrQueuedOperationsOfType(Constants.MICROSTUCTURE_OPERATION_TYPE);
    }
     **/

}
