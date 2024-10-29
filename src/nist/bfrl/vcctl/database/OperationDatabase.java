/*
 * OperationDatabase.java
 *
 * Created on April 28, 2005, 3:03 PM
 */
package nist.bfrl.vcctl.database;

import java.util.*;
import java.sql.*;
import java.io.*;

import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.exceptions.SQLDuplicatedKeyException;

import nist.bfrl.vcctl.util.*;
import nist.bfrl.vcctl.application.Vcctl;

/**
 *
 * @author tahall
 */
public class OperationDatabase {

    /** Creates a new instance of OperationDatabase */
    public OperationDatabase() {
    }

    static private Connection getConnection() throws SQLException {
        VCCTLDatabase.loadDriver();
        Connection cxn = null;
        String url = "jdbc:derby:" + Vcctl.getDBDirectory() + "vcctl_operation";
        cxn = DriverManager.getConnection(url);
        return cxn;
    }

    static public boolean isUniqueOperationNameForUser(String opname, String userName) throws SQLException, SQLArgumentException {
        if (userName == null || userName.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (opname == null || opname.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The operation name is empty");
        }
        PreparedStatement pstmt;
        String query = "SELECT type FROM " + Constants.OPERATION_TABLE_NAME + " WHERE name = ? AND username = ?";
        ResultSet rs = null;
        boolean retval = true;
        Connection connection = getConnection();
        pstmt = connection.prepareStatement(query);
        pstmt.setString(1, opname);
        pstmt.setString(2, userName);
        rs = pstmt.executeQuery();
        int row_count = 0;
        while (rs.next()) {
            row_count++;
        }

        if (row_count > 0) {
            retval = false;
        }
        rs.close();
        pstmt.close();
        connection.close();

        return retval;
    }

    /*
    static public boolean isUniqueProfileName(String profname) throws SQLException, SQLArgumentException {
    if (profname == null || profname.equalsIgnoreCase("")) {
    throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The profile name is empty");
    }
    PreparedStatement pstmt;
    String query = "SELECT * FROM " + Constants.PROFILE_TABLE_NAME + " WHERE name = ?";
    ResultSet rs = null;
    boolean retval = true;

    Connection connection = getConnection();
    pstmt = connection.prepareStatement(query);
    pstmt.setString(1, profname);
    rs = pstmt.executeQuery();
    if (rs.first()) {
    retval = false;
    }
    rs.close();
    pstmt.close();
    connection.close();

    return retval;
    }
     **/
    public static Operation getOperationForUser(String name, String userName) throws SQLException, SQLArgumentException {
        if (userName == null || userName.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }

        String changedname = name;
        if (changedname == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The operation name is empty");
        }

        String sql_getop = "SELECT * FROM " + Constants.OPERATION_TABLE_NAME + " WHERE name = ? AND username = ?";
        Operation retop = null;

        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql_getop);

        pstmt.setString(1, changedname);
        pstmt.setString(2, userName);
        ResultSet rs = pstmt.executeQuery();
        if (rs.next()) {
            retop = fromResultSet(rs);
        } else {
            rs.close();
            pstmt.close();
            pstmt = connection.prepareStatement(sql_getop);
            changedname = name.replace("/","\\");
            pstmt.setString(1, changedname);
            pstmt.setString(2, userName);
            rs = pstmt.executeQuery();
            if (rs.next()) {
                retop = fromResultSet(rs);
            }
        }
        rs.close();
        pstmt.close();
        connection.close();
        return retop;
    }
    /*
    private static HashMap opmap = new HashMap();
    static {
    opmap.put("psd sample",  "sample_operation");
    opmap.put("microstructure", "microstructure_operation");
    opmap.put("hydration", "hydration_operation");
    }*/

    public static void deleteOperationForUser(String name, String userName) throws SQLException, SQLArgumentException {
        // Get the type of this operation, find corresponding
        // table for output
        Operation thisop = getOperationForUser(name, userName);

        // Delete all operation data
        deleteOperationDataForUser(name, userName);
        String altname = name.replace("/","\\");

        // Delete entry FROM " + Constants.OPERATION_TABLE_NAME + " table
        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement("DELETE FROM " + Constants.OPERATION_TABLE_NAME + " WHERE name = ? AND username = ?");
        pstmt.setString(1, altname);
        pstmt.setString(2, userName);
        pstmt.executeUpdate();
        pstmt.close();
        pstmt = connection.prepareStatement("DELETE FROM " + Constants.OPERATION_TABLE_NAME + " WHERE name = ? AND username = ?");
        pstmt.setString(1, name);
        pstmt.setString(2, userName);
        pstmt.executeUpdate();
        pstmt.close();
        connection.close();

    }

    private static boolean deleteOperationDataForUser(String opname, String userName) {
        return ServerFile.deleteOperationDirForUser(opname, userName);
    }

    static public void queueOperation(Operation op) throws SQLDuplicatedKeyException, SQLException, SQLArgumentException {
        String name = op.getName();
        String user = op.getUsername();
        if (!OperationDatabase.isUniqueOperationNameForUser(name, user)) {
            throw new SQLDuplicatedKeyException(Constants.OPERATION_TABLE_NAME,
                    name, user,
                    "There already is an operation called '" + name + "' for '" + user + "' in the database.");
        }
        String datetime = Util.currentDateTime();
        String sql;
        sql = "INSERT INTO " + Constants.OPERATION_TABLE_NAME + " (name, username, type, queue, status, depends_on_operation_name, depends_on_operation_username, state, notes) VALUES(?,?,?,?,?,?,?,?,?)";

        Connection connection = getConnection();
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        pstmt.setString(2, user);
        pstmt.setString(3, op.getType());
        pstmt.setString(4, datetime);
        pstmt.setString(5, Constants.OPERATION_QUEUED_STATUS);
        pstmt.setString(6, op.getDepends_on_operation_name());
        pstmt.setString(7, op.getDepends_on_operation_username());
        pstmt.setBytes(8, op.getState());
        pstmt.setString(9, op.getNotes());
        pstmt.executeUpdate();
        pstmt.close();
        connection.close();
    }

    static public void startOperationForUser(String name, String userName) throws SQLException, SQLArgumentException {
        if (userName == null || userName.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The operation name is empty");
        }
        String datetime = Util.currentDateTime();
        String sql = "UPDATE " + Constants.OPERATION_TABLE_NAME + " SET status=?, start=? WHERE name=? AND username = ?";

        Connection connection = getConnection();
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, Constants.OPERATION_RUNNING_STATUS);
        pstmt.setString(2, datetime);
        pstmt.setString(3, name);
        pstmt.setString(4, userName);
        pstmt.executeUpdate();
        pstmt.close();
        connection.close();
    }

    static public void saveFinishedOperationForUser(String name, String userName) throws SQLException, SQLArgumentException {
        if (userName == null || userName.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The operation name is empty");
        }
        String datetime = Util.currentDateTime();
        String sql = "UPDATE " + Constants.OPERATION_TABLE_NAME + " SET status=?, finish=? WHERE name=? AND username = ?";

        Connection connection = getConnection();
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, Constants.OPERATION_FINISHED_STATUS);
        pstmt.setString(2, datetime);
        pstmt.setString(3, name);
        pstmt.setString(4, userName);
        pstmt.executeUpdate();
        pstmt.close();
        connection.close();
    }

    static public void cancelOperationForUser(String name, String userName) throws SQLException, SQLArgumentException {
        if (userName == null || userName.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The operation name is empty");
        }
        String datetime = Util.currentDateTime();
        String sql = "UPDATE " + Constants.OPERATION_TABLE_NAME + " SET status=?, finish=? WHERE name=? AND username = ?";

        Connection connection = getConnection();
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, Constants.OPERATION_CANCELLED_STATUS);
        pstmt.setString(2, datetime);
        pstmt.setString(3, name);
        pstmt.setString(4, userName);
        pstmt.executeUpdate();
        pstmt.close();
        connection.close();
    }

    static public String nameMostRecent(String username, String type) throws SQLException, SQLArgumentException {
        if (username == null || username.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (type == null || type.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The operation type is empty");
        }
        String sql_most_recent_name =
                "SELECT name FROM " + Constants.OPERATION_TABLE_NAME + " WHERE type=? AND username=? ORDER BY finish DESC";
        /**
         * List of all operation names of a given
         * type of operation.
         */
        String name = null;
        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql_most_recent_name);
        pstmt.setString(1, type);
        pstmt.setString(2, username);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            name = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return name;
    }

    static public List<Operation> mostRecentOperations(String username, int number) throws SQLException, SQLArgumentException {
        if (username == null || username.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        /**
         * List of most recent operations.
         */
        ArrayList<Operation> ops = new ArrayList();
        String sql_mr_ops = "SELECT * FROM " + Constants.OPERATION_TABLE_NAME + " WHERE username=? ORDER BY queue DESC";

        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql_mr_ops);
        pstmt.setString(1, username);
        pstmt.setInt(2, number);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            ops.add(fromResultSet(rs));
        }
        rs.close();
        pstmt.close();
        connection.close();

        return ops;
    }

    static private Operation fromResultSet(ResultSet rs) throws SQLException {

        String origname = rs.getString("name");
        String userName = rs.getString("username");
        String type = rs.getString("type");
        Operation retop = new Operation(origname, userName, type);
        retop.setQueue(rs.getTimestamp("queue"));
        if (rs.getObject("start") == null) {
            retop.setStart(null);
        } else {
            retop.setStart(rs.getTimestamp("start"));
        }

        if (rs.getObject("finish") == null) {
            retop.setFinish(null);
        } else {
            retop.setFinish(rs.getTimestamp("finish"));
        }
        retop.setStatus(rs.getString("status"));
        retop.setDepends_on_operation_name(rs.getString("depends_on_operation_name"));
        retop.setDepends_on_operation_username(rs.getString("depends_on_operation_username"));
        retop.setState(rs.getBytes("state"));
        return retop;

    }

    static private Operation fromResultSetChangeSeparator(ResultSet rs) throws SQLException {

        String origname = rs.getString("name");
        String name = origname.replace("\\","/");
        String userName = rs.getString("username");
        String type = rs.getString("type");
        Operation retop = new Operation(name, userName, type);
        retop.setQueue(rs.getTimestamp("queue"));
        if (rs.getObject("start") == null) {
            retop.setStart(null);
        } else {
            retop.setStart(rs.getTimestamp("start"));
        }

        if (rs.getObject("finish") == null) {
            retop.setFinish(null);
        } else {
            retop.setFinish(rs.getTimestamp("finish"));
        }
        retop.setStatus(rs.getString("status"));
        retop.setDepends_on_operation_name(rs.getString("depends_on_operation_name"));
        retop.setDepends_on_operation_username(rs.getString("depends_on_operation_username"));
        retop.setState(rs.getBytes("state"));
        return retop;

    }

    /*
    static public List finishedOperationsOfType(String type) {
    String sql_names_of_type =
    "SELECT name FROM " + Constants.OPERATION_TABLE_NAME + " WHERE type=? AND status=? ORDER BY finish DESC";
    /**
     * List of all operation names of a given
     * type of operation.
     */
    /*
    ArrayList names = new ArrayList();
    Connection connection = getConnection();
    try {
    PreparedStatement pstmt;
    pstmt = connection.prepareStatement(sql_names_of_type);
    pstmt.setString(1,  type);
    pstmt.setString(2, Constants.OPERATION_FINISHED_STATUS);
    ResultSet rs = pstmt.executeQuery();
    while (rs.next()) {
    names.add(rs.getString(1));
    }
    rs.close();
    pstmt.close();
    connection.close();
    } catch (SQLException e) {
    e.printStackTrace();
    throw new RuntimeException();
    }
    return names;
    }
     **/
    static public List<String> finishedOperationsNamesOfTypeForUser(String type, String user) throws SQLException, SQLArgumentException {
        if (user == null || user.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (type == null || type.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The operation type is empty");
        }
        String sql_names_of_type = "SELECT name FROM " + Constants.OPERATION_TABLE_NAME + " WHERE username=? AND type=? AND status=? ORDER BY finish DESC";
        /**
         * List of all operation names of a given
         * type of operation.
         */
        ArrayList<String> names = new ArrayList();
        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql_names_of_type);
        pstmt.setString(1, user);
        pstmt.setString(2, type);
        pstmt.setString(3, Constants.OPERATION_FINISHED_STATUS);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            names.add(rs.getString(1));
        }
        rs.close();
        pstmt.close();
        connection.close();
        return names;
    }

    static public List<Operation> finishedOperationsOfTypeForUser(String type, String user) throws SQLException, SQLArgumentException {
        if (user == null || user.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (type == null || type.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The operation type is empty");
        }
        String sql_names_of_type =
                "SELECT name FROM " + Constants.OPERATION_TABLE_NAME + " WHERE username=? AND type=? AND status=? ORDER BY finish DESC";
        /**
         * List of all operation names of a given
         * type of operation.
         */
        ArrayList<Operation> operations = new ArrayList();
        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql_names_of_type);
        pstmt.setString(1, user);
        pstmt.setString(2, type);
        pstmt.setString(3, Constants.OPERATION_FINISHED_STATUS);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            operations.add(fromResultSet(rs));
        }
        rs.close();
        pstmt.close();
        connection.close();
        return operations;
    }

    static public List<String> runningOperationsNamesOfTypeForUser(String type, String user) throws SQLException, SQLArgumentException {
        if (user == null || user.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (type == null || type.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The operation type is empty");
        }
        String sql_names_of_type = "SELECT name FROM " + Constants.OPERATION_TABLE_NAME + " WHERE username=? AND type=? AND status=? ORDER BY finish DESC";
        /**
         * List of all operation names of a given
         * type of operation.
         */
        ArrayList<String> names = new ArrayList();
        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql_names_of_type);
        pstmt.setString(1, user);
        pstmt.setString(2, type);
        pstmt.setString(3, Constants.OPERATION_RUNNING_STATUS);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            names.add(rs.getString(1));
        }
        rs.close();
        pstmt.close();
        connection.close();
        return names;
    }

    static public List<Operation> runningOperationsOfTypeForUser(String type, String user) throws SQLException, SQLArgumentException {
        if (user == null || user.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (type == null || type.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The operation type is empty");
        }
        String sql_names_of_type =
                "SELECT name FROM " + Constants.OPERATION_TABLE_NAME + " WHERE username=? AND type=? AND status=? ORDER BY finish DESC";
        /**
         * List of all operation names of a given
         * type of operation.
         */
        ArrayList<Operation> operations = new ArrayList();
        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql_names_of_type);
        pstmt.setString(1, user);
        pstmt.setString(2, type);
        pstmt.setString(3, Constants.OPERATION_RUNNING_STATUS);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            operations.add(fromResultSet(rs));
        }
        rs.close();
        pstmt.close();
        connection.close();
        return operations;
    }

    /*
    static public List finishedRunningOrQueuedOperationsOfType(String type) {
    String sql_names_of_type =
    "SELECT name FROM " + Constants.OPERATION_TABLE_NAME + " WHERE type=? AND (status=? OR status=? OR status=?) ORDER BY queue DESC";
    /**
     * List of all operation names of a given
     * type of operation.
     */
    /*
    ArrayList names = new ArrayList();
    Connection connection = getConnection();
    try {
    PreparedStatement pstmt;
    pstmt = connection.prepareStatement(sql_names_of_type);
    pstmt.setString(1,  type);
    pstmt.setString(2, Constants.OPERATION_FINISHED_STATUS);
    pstmt.setString(3, Constants.OPERATION_RUNNING_STATUS);
    pstmt.setString(4, Constants.OPERATION_QUEUED_STATUS);
    ResultSet rs = pstmt.executeQuery();
    while (rs.next()) {
    names.add(rs.getString(1));
    }
    rs.close();
    pstmt.close();
    connection.close();
    } catch (SQLException e) {
    e.printStackTrace();
    throw new RuntimeException();
    }
    return names;
    }
     **/
    static public List<String> finishedRunningOrQueuedOperationsNamesOfTypeForUser(String type, String user) throws SQLException, SQLArgumentException {
        if (user == null || user.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (type == null || type.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The operation type is empty");
        }
        String sql_names_of_type =
                "SELECT name FROM " + Constants.OPERATION_TABLE_NAME + " WHERE username=? AND type=? AND (status=? OR status=? OR status=?) ORDER BY queue DESC";
        /**
         * List of all operation names of a given
         * type of operation.
         */
        ArrayList<String> names = new ArrayList();
        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql_names_of_type);
        pstmt.setString(1, user);
        pstmt.setString(2, type);
        pstmt.setString(3, Constants.OPERATION_FINISHED_STATUS);
        pstmt.setString(4, Constants.OPERATION_RUNNING_STATUS);
        pstmt.setString(5, Constants.OPERATION_QUEUED_STATUS);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            names.add(rs.getString(1));
        }
        rs.close();
        pstmt.close();
        connection.close();
        return names;
    }

    static public List<Operation> finishedRunningOrQueuedOperationsOfTypeForUser(String type, String user) throws SQLException, SQLArgumentException {
        if (user == null || user.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (type == null || type.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The operation type is empty");
        }
        String sql_names_of_type =
                "SELECT name FROM " + Constants.OPERATION_TABLE_NAME + " WHERE username=? AND type=? AND (status=? OR status=? OR status=?) ORDER BY queue DESC";
        /**
         * List of all operation names of a given
         * type of operation.
         */
        ArrayList<Operation> operations = new ArrayList();
        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql_names_of_type);
        pstmt.setString(1, user);
        pstmt.setString(2, type);
        pstmt.setString(3, Constants.OPERATION_FINISHED_STATUS);
        pstmt.setString(4, Constants.OPERATION_RUNNING_STATUS);
        pstmt.setString(5, Constants.OPERATION_QUEUED_STATUS);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            operations.add(fromResultSet(rs));
        }
        rs.close();
        pstmt.close();
        connection.close();
        return operations;
    }

    public static List<Operation> getOperationsByStatusForUser(String status, String order_by, String username) throws SQLException, SQLArgumentException {
        if (username == null || username.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (status == null || status.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "status", "The operation status is empty");
        }
        ArrayList<Operation> ops = new ArrayList();

        String sql = "SELECT * FROM " + Constants.OPERATION_TABLE_NAME + " WHERE username=? AND status=? ORDER BY " + order_by + " DESC";
        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, username);
        pstmt.setString(2, status);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            ops.add(fromResultSet(rs));
        }
        rs.close();
        pstmt.close();
        connection.close();

        return ops;
    }

    public static List<Operation> getOperationsByStatusForUserChangeSeparator(String status, String order_by, String username) throws SQLException, SQLArgumentException {
        if (username == null || username.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (status == null || status.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "status", "The operation status is empty");
        }
        ArrayList<Operation> ops = new ArrayList();

        String sql = "SELECT * FROM " + Constants.OPERATION_TABLE_NAME + " WHERE username=? AND status=? ORDER BY " + order_by + " DESC";
        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, username);
        pstmt.setString(2, status);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            ops.add(fromResultSetChangeSeparator(rs));
        }
        rs.close();
        pstmt.close();
        connection.close();

        return ops;
    }

    /*
    public static List getOperationsForUser(String order_by, String username) {
    ArrayList ops = new ArrayList();

    String sql = "SELECT * FROM " + Constants.OPERATION_TABLE_NAME + " WHERE username=? ORDER BY "+order_by+" DESC";
    try {
    Connection connection = getConnection();
    PreparedStatement pstmt;
    pstmt = connection.prepareStatement(sql);
    pstmt.setString(1, username);
    ResultSet rs = pstmt.executeQuery();
    while (rs.next()) {
    ops.add(fromResultSet(rs));
    }
    rs.close();
    pstmt.close();
    connection.close();
    } catch (SQLException e) {
    e.printStackTrace();
    throw new RuntimeException();
    }

    return ops;
    }
     **/

    public static Map<String, Operation> getOperationsOfTypeForUser(String type, String order_by, String username) throws SQLException, SQLArgumentException {
        if (username == null || username.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (type == null || type.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The operation type is empty");
        }
        HashMap<String, Operation> ops = new HashMap();
        Operation op;

        String sql = "SELECT * FROM " + Constants.OPERATION_TABLE_NAME + " WHERE username=? AND type=? ORDER BY " + order_by + " DESC";

        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, username);
        pstmt.setString(2, type);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            op = fromResultSet(rs);
            ops.put(op.getEscapedName(), op);
        }
        rs.close();
        pstmt.close();
        connection.close();

        return ops;
    }

    public static Map<String, Operation> getOperationsOfTypeForUserChangeSeparator(String type, String order_by, String username) throws SQLException, SQLArgumentException {
        if (username == null || username.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (type == null || type.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The operation type is empty");
        }
        HashMap<String, Operation> ops = new HashMap();
        Operation op;

        String sql = "SELECT * FROM " + Constants.OPERATION_TABLE_NAME + " WHERE username=? AND type=? ORDER BY " + order_by + " DESC";

        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, username);
        pstmt.setString(2, type);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            op = fromResultSetChangeSeparator(rs);
            ops.put(op.getEscapedName(), op);
        }
        rs.close();
        pstmt.close();
        connection.close();

        return ops;
    }

    /*
    public static int getOperationCountByStatus(String status) {
    List l = getOperationsByStatus(status, "queue");

    return l.size();
    }
     **/
    public static String getOperationStatusForUser(String name, String userName) throws SQLException, SQLArgumentException {
        if (userName == null || userName.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The operation name is empty");
        }
        String sql = "SELECT status FROM " + Constants.OPERATION_TABLE_NAME + " WHERE name=? AND username = ?";
        String status = null;

        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        pstmt.setString(2, userName);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            status = rs.getString(1).trim();
        }
        rs.close();
        pstmt.close();
        connection.close();

        return status;
    }

    public static String getDependantOperationForUser(String name, String userName) throws SQLException, SQLArgumentException {
        if (userName == null || userName.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "username", "The operation user name is empty");
        }
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The operation name is empty");
        }
        String sql = "SELECT depends_on_operation_name FROM " + Constants.OPERATION_TABLE_NAME + " WHERE name=? AND username = ?";
        String status = null;

        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        pstmt.setString(2, userName);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            status = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();

        return status;
    }
}
