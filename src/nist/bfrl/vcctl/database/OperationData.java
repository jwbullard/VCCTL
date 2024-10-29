/*
 * OperationData.java
 *
 * Created on July 11, 2005, 3:45 PM
 */

package nist.bfrl.vcctl.database;

import java.sql.*;

/**
 *
 * @author tahall
 */
public interface OperationData {
    public abstract String type();
    
    public abstract PreparedStatement queueInsertStatement(Connection connection);
    public abstract PreparedStatement startUpdateStatement(Connection connection);
    public abstract PreparedStatement runningUpdateStatement(Connection connection);
    public abstract PreparedStatement finishUpdateStatement(Connection connection);
}
