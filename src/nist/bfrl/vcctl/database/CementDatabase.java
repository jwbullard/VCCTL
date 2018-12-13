/*
 * CementDatabase.java
 *
 * Created on April 1, 2005, 3:32 PM
 */
package nist.bfrl.vcctl.database;

import java.util.*;
import java.sql.*;
import java.io.*;
import java.util.logging.Level;
import java.util.logging.Logger;
import nist.bfrl.vcctl.exceptions.*;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.ServerFile;
import nist.bfrl.vcctl.application.Vcctl;
import org.apache.derby.jdbc.EmbeddedDriver;
import org.apache.struts.action.*;

/**
 *
 * @author tahall
 */
public class CementDatabase {

    /** Creates a new instance of CementDatabase */
    public CementDatabase() {
    }

    static protected Connection getConnection() throws SQLException {
        VCCTLDatabase.loadDriver();
        Connection cxn = null;
        String url = "jdbc:derby:" + Vcctl.getDBDirectory() + "vcctl_cement";
        cxn = DriverManager.getConnection(url);

        return cxn;
    }

    static public boolean isUniqueMaterialNameOfType(String materialType, String name) throws SQLArgumentException, SQLException {
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The name is empty");
        }
        PreparedStatement pstmt;
        String query = "SELECT name FROM " + materialType + " WHERE name = ?";
        ResultSet rs = null;
        boolean retval = true;
        Connection connection = getConnection();
        pstmt = connection.prepareStatement(query);
        pstmt.setString(1, name);
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

    static public boolean isUniqueMaterialDisplayNameOfType(String materialType, String name) throws SQLArgumentException, SQLException {

        if (materialType.equals(Constants.AGGREGATE_TABLE_NAME)) {
            if (name == null || name.equalsIgnoreCase("")) {
                throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The name is empty");
            }
            PreparedStatement pstmt;
            String query = "SELECT display_name FROM " + materialType + " WHERE display_name = ?";
            ResultSet rs = null;
            boolean retval = true;
            Connection connection = getConnection();
            pstmt = connection.prepareStatement(query);
            pstmt.setString(1, name);
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
        } else {
            return true;
        }
    }

    private static String getFirstMaterialNameOfType(String type) throws SQLException, SQLArgumentException {
        if (type == null || type.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The type is empty");
        }
        Connection connection = getConnection();
        String name = "";
        String sql = "SELECT name FROM " + type;
        PreparedStatement pstmt = connection.prepareStatement(sql);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            name = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return name;
    }

    private static String getFirstMaterialDisplayNameOfType(String type) throws SQLException, SQLArgumentException {
        if (type.equals(Constants.AGGREGATE_TABLE_NAME)) {
            Connection connection = getConnection();
            String name = "";
            String sql = "SELECT display_name FROM " + type;
            PreparedStatement pstmt = connection.prepareStatement(sql);
            ResultSet rs = pstmt.executeQuery();
            while (rs.next()) {
                name = rs.getString(1);
            }
            rs.close();
            pstmt.close();
            connection.close();
            return name;
        } else {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The type is empty");
        }
    }

    private static String getFirstDBFileNameOfType(String type) throws SQLException, SQLArgumentException {
        if (type == null || type.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The type is empty");
        }
        Connection connection = getConnection();
        String name = "";
        String sql = "SELECT name FROM " + Constants.DB_FILE_TABLE_NAME + " WHERE type = ?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, type);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            name = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return name;
    }

    private static void deleteEntryFromTable(String table, String key, String value) throws SQLException {
        Connection connection = getConnection();
        String sqlcmd = "DELETE FROM " + table +
                " WHERE " + key + "=?";
        PreparedStatement pstmt = connection.prepareStatement(sqlcmd);
        pstmt.setString(1, value);
        pstmt.executeUpdate();
        pstmt.close();
        connection.close();
    }

    private static void deleteEntryOfNameFromTable(String table, String name) throws SQLException {
        deleteEntryFromTable(table, "name", name);
    }

     private static void deleteEntryOfDisplayNameFromTable(String table, String display_name) throws SQLException {
        deleteEntryFromTable(table, "display_name", display_name);
    }

    /**
     * Retrieve a list of names of files from the db_file
     * table that match a given type.  The db_file table
     * contains characteristic files of various types, including
     * alkali characteristics for cement and fly ash, temperature
     * schedules, and slag characteristics.
     */
    private static List<String> getNamesOfType(String type) throws SQLArgumentException, SQLException {
        if (type == null || type.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The type is empty");
        }
        Connection connection = getConnection();
        ArrayList<String> names = new ArrayList();
        String sql = "SELECT name FROM " + Constants.DB_FILE_TABLE_NAME + " WHERE type=?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, type);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            names.add(rs.getString(1));
        }
        rs.close();
        pstmt.close();
        connection.close();
        return names;
    }

    private static List<String> getNamesInTable(String table) throws SQLException {
        return getNamesInTable(table, "");
    }

    private static List<String> getNamesInTable(String table, String orderBy) throws SQLException {
        Connection connection = getConnection();
        ArrayList<String> names = new ArrayList();
        String sql = "SELECT name FROM " + table;
        if (!orderBy.equalsIgnoreCase("")) {
            sql += " ORDER BY " + orderBy;
        }
        PreparedStatement pstmt = connection.prepareStatement(sql);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            names.add(rs.getString(1));
        }
        rs.close();
        pstmt.close();
        connection.close();
        return names;
    }

    public static List<String> getCementNames() throws NoCementException, SQLException {
        List<String> names = getNamesInTable(Constants.CEMENT_TABLE_NAME);

        if (names == null || names.size() == 0) {
            throw new NoCementException("No cement has been found in the database.");
        }
        return names;
    }

    static public boolean isUniqueCementName(String name) throws SQLArgumentException, SQLException {
        return isUniqueMaterialNameOfType(Constants.CEMENT_TABLE_NAME, name);
    }

    static public boolean cementExists(String name) throws SQLArgumentException, SQLException {
        return !isUniqueCementName(name);
    }

    public static String getFirstCementName() throws NoCementException, SQLException {
        String name = null;
        try {
            name = getFirstMaterialNameOfType(Constants.CEMENT_TABLE_NAME);
        } catch (SQLArgumentException ex) {
            Logger.getLogger(CementDatabase.class.getName()).log(Level.SEVERE, null, ex);
        }
        if (name == null || name.equalsIgnoreCase("")) {
            throw new NoCementException("No cement has been found in the database.");
        }
        return name;
    }

    public static List<String> getFlyAshNames() throws NoFlyAshException, SQLException {
        List<String> names = getNamesInTable(Constants.FLY_ASH_TABLE_NAME);

        if (names == null || names.size() == 0) {
            throw new NoFlyAshException("No fly ash has been found in the database.");
        }
        return names;
    }

    static public boolean isUniqueFlyAshName(String name) throws SQLArgumentException, SQLException {
        return isUniqueMaterialNameOfType(Constants.FLY_ASH_TABLE_NAME, name);
    }

    static public boolean flyAshExists(String name) throws SQLArgumentException, SQLException {
        return !isUniqueFlyAshName(name);
    }

    public static String getFirstFlyAshName() throws NoFlyAshException, SQLException {
        String name = null;
        try {
            name = getFirstMaterialNameOfType(Constants.FLY_ASH_TABLE_NAME);
        } catch (SQLArgumentException ex) {
            Logger.getLogger(CementDatabase.class.getName()).log(Level.SEVERE, null, ex);
        }
        if (name == null || name.equalsIgnoreCase("")) {
            throw new NoFlyAshException("No fly ash has been found in the database.");
        }
        return name;
    }

    public static List<String> getSlagNames() throws NoSlagException, SQLException {
        List<String> names = getNamesInTable(Constants.SLAG_TABLE_NAME);

        if (names == null || names.size() == 0) {
            throw new NoSlagException("No slag has been found in the database.");
        }
        return names;
    }

    static public boolean isUniqueSlagName(String name) throws SQLArgumentException, SQLException {
        return isUniqueMaterialNameOfType(Constants.SLAG_TABLE_NAME, name);
    }

    static public boolean slagExists(String name) throws SQLArgumentException, SQLException {
        return !isUniqueSlagName(name);
    }

    public static String getFirstSlagName() throws NoSlagException, SQLException {
        String name = null;
        try {
            name = getFirstMaterialNameOfType(Constants.SLAG_TABLE_NAME);
        } catch (SQLArgumentException ex) {
            Logger.getLogger(CementDatabase.class.getName()).log(Level.SEVERE, null, ex);
        }
        if (name == null || name.equalsIgnoreCase("")) {
            throw new NoSlagException("No slag has been found in the database.");
        }
        return name;
    }

    public static List<String> getInertFillerNames() throws NoInertFillerException, SQLException {
        List<String> names = getNamesInTable(Constants.INERT_FILLER_TABLE_NAME);

        if (names == null || names.size() == 0) {
            throw new NoInertFillerException("No inert filler has been found in the database.");
        }
        return names;
    }

    static public boolean isUniqueInertFillerName(String name) throws SQLArgumentException, SQLException {
        return isUniqueMaterialNameOfType(Constants.INERT_FILLER_TABLE_NAME, name);
    }

    static public boolean inertFillerExists(String name) throws SQLArgumentException, SQLException {
        return !isUniqueInertFillerName(name);
    }

    public static String getFirstInertFillerName() throws NoInertFillerException, SQLException {
        String name = null;
        try {
            name = getFirstMaterialNameOfType(Constants.INERT_FILLER_TABLE_NAME);
        } catch (SQLArgumentException ex) {
            Logger.getLogger(CementDatabase.class.getName()).log(Level.SEVERE, null, ex);
        }
        if (name == null || name.equalsIgnoreCase("")) {
            throw new NoInertFillerException("No inert filler has been found in the database.");
        }
        return name;
    }

    public static List<String> getParticleShapeSetNames() throws NoParticleShapeSetException, SQLException {
        List<String> names = getNamesInTable(Constants.PASRTICLE_SHAPE_SET_TABLE_NAME);

        if (names == null || names.size() == 0) {
            throw new NoParticleShapeSetException("No particle shape set has been found in the database.");
        }
        return names;
    }

    /*
    public static String getFirstCementDataFileName() throws SQLException, DBFileException {
    String name = null;
    try {
    String[] hydrationTypes = {Constants.CALORIMETRY_FILE_TYPE,
    Constants.CHEMICAL_SHRINKAGE_FILE_TYPE,
    Constants.PARAMETER_FILE_TYPE,
    Constants.TIMING_OUTPUT_FILE_TYPE};
    for (int i = 0; i < hydrationTypes.length && name == null; i++) {
    name = getFirstDBFileNameOfType(hydrationTypes[i]);
    }
    } catch (SQLArgumentException ex) {
    Logger.getLogger(CementDatabase.class.getName()).log(Level.SEVERE, null, ex);
    }
    if (name == null || name.equalsIgnoreCase("")) {
    throw new DBFileException(Constants.NO_DATA_OF_THIS_TYPE, "No cement data file has been found in the database.");
    }
    return name;
    }
     * */
    public static String getFirstCementDataFileName() throws SQLException, DBFileException {
        String name = null;
        try {
            name = getFirstMaterialNameOfType(Constants.DB_FILE_TABLE_NAME);
        } catch (SQLArgumentException ex) {
            Logger.getLogger(CementDatabase.class.getName()).log(Level.SEVERE, null, ex);
        }
        if (name == null || name.equalsIgnoreCase("")) {
            throw new DBFileException(Constants.NO_DATA_OF_THIS_TYPE, "No cement data file has been found in the database.");
        }
        return name;
    }

    public static String getFirstPSDName() throws DBFileException, SQLException {
        String name = null;
        try {
            name = getFirstDBFileNameOfType(Constants.PSD_TYPE);
        } catch (SQLArgumentException ex) {
            Logger.getLogger(CementDatabase.class.getName()).log(Level.SEVERE, null, ex);
        }
        if (name == null || name.equalsIgnoreCase("")) {
            throw new DBFileException(Constants.NO_DATA_OF_THIS_TYPE, Constants.PSD_TYPE, "No PSD has been found in the database.");
        }
        return name;
    }

    static public boolean isUniqueDBFileName(String name) throws SQLArgumentException, SQLException {
        return isUniqueMaterialNameOfType(Constants.DB_FILE_TABLE_NAME, name);
    }

    static public boolean dbFileExists(String name) throws SQLArgumentException, SQLException {
        return !isUniqueDBFileName(name);
    }

    static public boolean isUniqueAggregateName(String name) throws SQLArgumentException, SQLException {
        return isUniqueMaterialNameOfType(Constants.AGGREGATE_TABLE_NAME, name);
    }

    static public boolean isUniqueAggregateDisplayName(String displayname) throws SQLArgumentException, SQLException {
        return isUniqueMaterialDisplayNameOfType(Constants.AGGREGATE_TABLE_NAME, displayname);
    }

    static public boolean aggregateExists(String displayname) throws SQLArgumentException, SQLException {
        return !isUniqueAggregateName(displayname);
    }

    public static List<String> getAggregateNamesOfType(int aggregateType) throws SQLArgumentException, SQLException {
        if (aggregateType != 0 && aggregateType != 1) {
            throw new SQLArgumentException(Constants.ARGUMENT_VALUE_NOT_ALLOWED, "type",
                    "The type of the aggregate must be either 0 (fine) or 1 (coarse).");
        }
        Connection connection = getConnection();
        ArrayList<String> names = new ArrayList();

        String sql = "SELECT name FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE aggregate_type = " + aggregateType;
        PreparedStatement pstmt = connection.prepareStatement(sql);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            names.add(rs.getString(1));
        }
        rs.close();
        pstmt.close();
        connection.close();
        return names;
    }

    public static List<String> getAggregateDisplayNamesOfType(int aggregateType) throws SQLArgumentException, SQLException {
        if (aggregateType != 0 && aggregateType != 1) {
            throw new SQLArgumentException(Constants.ARGUMENT_VALUE_NOT_ALLOWED, "type",
                    "The type of the aggregate must be either 0 (fine) or 1 (coarse).");
        }
        Connection connection = getConnection();
        ArrayList<String> names = new ArrayList();

        String sql = "SELECT display_name FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE aggregate_type = " + aggregateType;
        PreparedStatement pstmt = connection.prepareStatement(sql);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            names.add(rs.getString(1));
        }
        rs.close();
        pstmt.close();
        connection.close();
        return names;
    }

    public static List<String> getFineAggregateNames() throws NoFineAggregateException, SQLArgumentException, SQLException {
        List<String> aggregatesList = null;
        aggregatesList = getAggregateNamesOfType(0);
        if (aggregatesList == null || aggregatesList.size() == 0) {
            throw new NoFineAggregateException("No fine aggregate has been found in the database.");
        }
        return aggregatesList;
    }

    public static List<String> getCoarseAggregateNames() throws NoCoarseAggregateException, SQLArgumentException, SQLException {
        List<String> aggregatesList = null;
        aggregatesList = getAggregateNamesOfType(1);
        if (aggregatesList == null || aggregatesList.size() == 0) {
            throw new NoCoarseAggregateException("No coarse aggregate has been found in the database.");
        }
        return aggregatesList;
    }

    public static List<String> getFineAggregateDisplayNames() throws NoFineAggregateException, SQLArgumentException, SQLException {
        List<String> aggregatesList = null;
        aggregatesList = getAggregateDisplayNamesOfType(0);
        if (aggregatesList == null || aggregatesList.size() == 0) {
            throw new NoFineAggregateException("No fine aggregate has been found in the database.");
        }
        return aggregatesList;
    }

    public static List<String> getCoarseAggregateDisplayNames() throws NoCoarseAggregateException, SQLArgumentException, SQLException {
        List<String> aggregatesList = null;
        aggregatesList = getAggregateDisplayNamesOfType(1);
        if (aggregatesList == null || aggregatesList.size() == 0) {
            throw new NoCoarseAggregateException("No coarse aggregate has been found in the database.");
        }
        return aggregatesList;
    }

    private static byte[] getBLOB(String sql, String name) throws SQLArgumentException, SQLException {
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The name is empty");
        }
        Connection connection = getConnection();
        byte[] data = null;
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        ResultSet rs = pstmt.executeQuery();
        if (rs.next()) {
            data = rs.getBytes(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return data;
    }

    public static byte[] getCementDBImage(String name) throws SQLArgumentException, SQLException {
        return getBLOB("SELECT gif FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?", name);
    }

    public static byte[] getAggregateDBImage(String name) throws SQLArgumentException, SQLException {
        return getBLOB("SELECT gif FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE display_name=?", name);
    }

    public static byte[] getAggregateImage(String name) throws SQLArgumentException, SQLException {
        return getBLOB("SELECT gif FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE display_name=?", name);
    }

    private static int getInt(String sql, String name) throws SQLArgumentException, SQLException {
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The name is empty");
        }
        Connection connection = getConnection();
        int result = 0;
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        ResultSet rs = pstmt.executeQuery();
        if (rs.next()) {
            result = rs.getInt(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return result;
    }

    private static double getDouble(String sql, String name) throws SQLArgumentException, SQLException {
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The name is empty");
        }
        Connection connection = getConnection();
        double result = 0.0;
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        ResultSet rs = pstmt.executeQuery();
        if (rs.next()) {
            result = rs.getDouble(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return result;
    }

    private static String getString(String sql, String name) throws SQLArgumentException, SQLException {
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The name is empty");
        }
        Connection connection = getConnection();
        String result = "";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        ResultSet rs = pstmt.executeQuery();
        if (rs.next()) {
            result = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return result;
    }

    public static byte[] getLegend(String name) throws SQLArgumentException, SQLException {
        return getBLOB("SELECT legend_gif FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?", name);
    }

    /*
    public static String getPSD(String name) throws SQLArgumentException {
    byte[] psdbytes = getBLOB("SELECT data FROM " + Constants.DB_FILE_TABLE_NAME + " WHERE name=?", name);
    if (psdbytes == null) {
    psdbytes = getBLOB("SELECT psd FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?", name);
    }
    return new String(psdbytes);
    }
     **/
    public static String getPfc(String name) throws SQLArgumentException, SQLException {
        byte bytes[] = getBLOB("SELECT pfc FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?", name);
        if (bytes == null) {
            return "0.0 0.0\n0.0 0.0\n0.0 0.0\n0.0 0.0";
        } else {
            return new String(bytes);
        }
    }

    public static String getSil(String name) throws SQLArgumentException, SQLException {
        byte bytes[] = getBLOB("SELECT sil FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?", name);
        if (bytes == null) {
            return null;
        } else {
            return new String(bytes);
        }
    }

    public static String getC3s(String name) throws SQLArgumentException, SQLException {
        byte bytes[] = getBLOB("SELECT c3s FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?", name);
        if (bytes == null) {
            return null;
        } else {
            return new String(bytes);
        }
    }

    public static String getC4f(String name) throws SQLArgumentException, SQLException {
        byte bytes[] = getBLOB("SELECT c4f FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?", name);
        if (bytes == null) {
            return null;
        } else {
            return new String(bytes);
        }
    }

    public static String getC3a(String name) throws SQLArgumentException, SQLException {
        byte bytes[] = getBLOB("SELECT c3a FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?", name);
        if (bytes == null) {
            return null;
        } else {
            return new String(bytes);
        }
    }

    public static String getN2o(String name) throws SQLArgumentException, SQLException {
        byte[] bytes = getBLOB("SELECT n2o FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?", name);
        if (bytes == null) {
            return null;
        } else {
            return new String(bytes);
        }
    }

    public static String getK2o(String name) throws SQLArgumentException, SQLException {
        byte[] bytes = getBLOB("SELECT k2o FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?", name);
        if (bytes == null) {
            return null;
        } else {
            return new String(bytes);
        }
    }

    public static String getAlu(String name) throws SQLArgumentException, SQLException {
        byte[] bytes = getBLOB("SELECT alu FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?", name);
        if (bytes == null) {
            return null;
        } else {
            return new String(bytes);
        }
    }

    public static double[] getSulfateFractions(String name) throws SQLArgumentException, SQLException {
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The name is empty");
        }
        Connection connection = getConnection();
        String sql = "SELECT dihyd, hemihyd, anhyd FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?";
        double[] frac = new double[3];
        frac[0] = 0.0;
        frac[1] = 0.0;
        frac[2] = 0.0;

        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        ResultSet rs = pstmt.executeQuery();
        if (rs.next()) {
            frac[0] = rs.getDouble("dihyd");
            frac[1] = rs.getDouble("hemihyd");
            frac[2] = rs.getDouble("anhyd");
        }
        rs.close();
        pstmt.close();
        connection.close();
        return frac;
    }

    public static String getType(String name) throws SQLArgumentException, SQLException {
        int type = getInt("SELECT type FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE name=?", name);
        return String.valueOf(type);
    }

    /*
    public static String getShapeSetPath(String aggregateName) {
    byte bytes[] = getBLOB("SELECT a_s_s.path FROM " + Constants.AGGREGATE_TABLE_NAME + " a, aggregate_shape_set a_s_s WHERE a.name=? AND a_s_s.name=a.shape_set_name", aggregateName);
    if (bytes == null) {
    return null;
    } else {
    return new String(bytes);
    }
    }

    public static List<String> getAggregateShapeSetsNamesOfType(int aggregateType) {
    Connection connection = getConnection();
    ArrayList<String> names = new ArrayList();
    try {
    String sql = "SELECT name FROM aggregate_shape_set WHERE aggregate_type = " + aggregateType;
    PreparedStatement pstmt = connection.prepareStatement(sql);
    ResultSet rs = pstmt.executeQuery();
    while (rs.next()) {
    names.add(rs.getString(1));
    }
    rs.close();
    pstmt.close();
    connection.close();
    return names;
    } catch (SQLException e) {
    e.printStackTrace();
    return null;
    }
    }

    public static List<String> getFineAggregateShapeSetsNames() {
    return getAggregateShapeSetsNamesOfType(0);
    }

    public static List<String> getCoarseAggregateShapeSetsNames() {
    return getAggregateShapeSetsNamesOfType(1);
    }
     **/
    static public boolean isUniqueGradingName(String name) throws SQLArgumentException, SQLException {
        return isUniqueMaterialNameOfType(Constants.GRADING_TABLE_NAME, name);
    }

    static public boolean gradingExists(String name) throws SQLArgumentException, SQLException {
        return !isUniqueGradingName(name);
    }

    public static String getGrading(String name) throws SQLArgumentException, SQLException {
        return new String(getGradingData(name));
    }

    public static byte[] getGradingData(String name) throws SQLArgumentException, SQLException {
        byte bytes[] = getBLOB("SELECT grading FROM " + Constants.GRADING_TABLE_NAME + " WHERE name=?", name);
        if (bytes == null) {
            return null;
        } else {
            return bytes;
        }
    }

    public static List<String> getGradingNamesOfType(int aggregateType) throws SQLException, SQLArgumentException {
        if (aggregateType != 0 && aggregateType != 1) {
            throw new SQLArgumentException(Constants.ARGUMENT_VALUE_NOT_ALLOWED, "type",
                    "The type of the aggregate must be either 0 (fine) or 1 (coarse).");
        }
        Connection connection = getConnection();
        ArrayList<String> names = new ArrayList();

        String sql = "SELECT name FROM " + Constants.GRADING_TABLE_NAME + " WHERE aggregate_type = " + aggregateType;
        PreparedStatement pstmt = connection.prepareStatement(sql);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            names.add(rs.getString(1));
        }
        rs.close();
        pstmt.close();
        connection.close();
        return names;
    }

    public static double getAggregateSpecificGravity(String aggregateName) throws SQLArgumentException, SQLException {
        return getDouble("SELECT specific_gravity FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE display_name=?", aggregateName);
    }

    public static String getAggregateShapeStats(String name) throws SQLArgumentException, SQLException {
        byte bytes[] = getBLOB("SELECT shape_stats FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE display_name=?", name);
        if (bytes == null) {
            return null;
        } else {
            return new String(bytes);
        }
    }

    public static String getFirstAggregateNameOfType(int aggregateType) throws SQLException, SQLArgumentException {
        if (aggregateType != 0 && aggregateType != 1) {
            throw new SQLArgumentException(Constants.ARGUMENT_VALUE_NOT_ALLOWED, "type",
                    "The type of the aggregate must be either 0 (fine) or 1 (coarse).");
        }
        Connection connection = getConnection();
        String name = "";

        String sql = "SELECT name FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE aggregate_type = " + aggregateType;
        PreparedStatement pstmt = connection.prepareStatement(sql);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            name = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return name;
    }

    public static String getFirstAggregateDisplayNameOfType(int aggregateType) throws SQLException, SQLArgumentException {
        if (aggregateType != 0 && aggregateType != 1) {
            throw new SQLArgumentException(Constants.ARGUMENT_VALUE_NOT_ALLOWED, "type",
                    "The type of the aggregate must be either 0 (fine) or 1 (coarse).");
        }
        Connection connection = getConnection();
        String displayname = "";

        String sql = "SELECT display_name FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE aggregate_type = " + aggregateType;
        PreparedStatement pstmt = connection.prepareStatement(sql);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            displayname = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return displayname;
    }

    public static String getFirstCoarseAggregateName() throws NoCoarseAggregateException, SQLException, SQLArgumentException {
        String firstAggregateName = getFirstAggregateNameOfType(1);
        if (firstAggregateName == null || firstAggregateName.equalsIgnoreCase("")) {
            throw new NoCoarseAggregateException("No coarse aggregate has been found in the database");
        }
        return firstAggregateName;
    }

    public static String getFirstFineAggregateName() throws NoFineAggregateException, SQLException, SQLArgumentException {
        String firstAggregateName = getFirstAggregateNameOfType(0);
        if (firstAggregateName == null || firstAggregateName.equalsIgnoreCase("")) {
            throw new NoFineAggregateException("No fine aggregate has been found in the database");
        }
        return firstAggregateName;
    }

    public static String getFirstCoarseAggregateDisplayName() throws NoCoarseAggregateException, SQLException, SQLArgumentException {
        String firstAggregateDisplayName = getFirstAggregateDisplayNameOfType(1);
        if (firstAggregateDisplayName == null || firstAggregateDisplayName.equalsIgnoreCase("")) {
            throw new NoCoarseAggregateException("No coarse aggregate has been found in the database");
        }
        return firstAggregateDisplayName;
    }

    public static String getFirstFineAggregateDisplayName() throws NoFineAggregateException, SQLException, SQLArgumentException {
        String firstAggregateDisplayName = getFirstAggregateDisplayNameOfType(0);
        if (firstAggregateDisplayName == null || firstAggregateDisplayName.equalsIgnoreCase("")) {
            throw new NoFineAggregateException("No fine aggregate has been found in the database");
        }
        return firstAggregateDisplayName;
    }

    public static String getFirstAggregateGradingNameOfType(int aggregateType) throws SQLException, SQLArgumentException {
        if (aggregateType != 0 && aggregateType != 1) {
            throw new SQLArgumentException(Constants.ARGUMENT_VALUE_NOT_ALLOWED, "type",
                    "The type of the aggregate must be either 0 (fine) or 1 (coarse).");
        }
        Connection connection = getConnection();
        String name = "";

        String sql = "SELECT name FROM " + Constants.GRADING_TABLE_NAME + " WHERE aggregate_type = " + aggregateType;
        PreparedStatement pstmt = connection.prepareStatement(sql);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            name = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return name;
    }

    public static String getFirstCoarseAggregateGradingName() throws NoCoarseAggregateGradingException, SQLException, SQLArgumentException {
        String gradingName = getFirstAggregateGradingNameOfType(1);
        if (gradingName == null || gradingName.equalsIgnoreCase("")) {
            throw new NoCoarseAggregateGradingException("No coarse aggregate grading has been found in the database.");
        }
        return gradingName;
    }

    public static String getFirstFineAggregateGradingName() throws NoFineAggregateGradingException, SQLException, SQLArgumentException {
        String gradingName = getFirstAggregateGradingNameOfType(0);
        if (gradingName == null || gradingName.equalsIgnoreCase("")) {
            throw new NoFineAggregateGradingException("No fine aggregate grading has been found in the database.");
        }
        return gradingName;
    }

    public static List<String> getFineAggregateGradingNames() throws NoFineAggregateGradingException, SQLException, SQLArgumentException {
        List<String> gradingsList = getGradingNamesOfType(0);
        if (gradingsList == null || gradingsList.size() == 0) {
            throw new NoFineAggregateGradingException("No fine aggregate grading has been found in the database.");
        }
        return gradingsList;
    }

    public static List<String> getCoarseAggregateGradingNames() throws NoCoarseAggregateGradingException, SQLException, SQLArgumentException {
        List<String> gradingsList = getGradingNamesOfType(1);
        if (gradingsList == null || gradingsList.size() == 0) {
            throw new NoCoarseAggregateGradingException("No coarse aggregate grading has been found in the database.");
        }
        return gradingsList;
    }

    public static String getAggregateNameWithDisplayName(String displayName) throws  SQLException, SQLArgumentException {
        PreparedStatement pstmt;
        String query = "SELECT name FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE display_name = ?";
        ResultSet rs = null;
        String namestr = null;
        boolean retval = true;
        Connection connection = getConnection();
        pstmt = connection.prepareStatement(query);
        pstmt.setString(1, displayName);
        rs = pstmt.executeQuery();
        while (rs.next()) {
            namestr = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return namestr;
    }

     public static String getAggregateDisplayNameWithName(String namestr) throws SQLException, SQLArgumentException {
        PreparedStatement pstmt;
        String query = "SELECT display_name FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE name = ?";
        ResultSet rs = null;
        String displaynamestr = null;
        boolean retval = true;
        Connection connection = getConnection();
        pstmt = connection.prepareStatement(query);
        pstmt.setString(1, namestr);
        rs = pstmt.executeQuery();
        while (rs.next()) {
            displaynamestr = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return displaynamestr;
    }

    public static double getGradingMaxDiameter(String gradingName) throws SQLArgumentException, SQLException {
        return getDouble("SELECT max_diameter FROM " + Constants.GRADING_TABLE_NAME + " WHERE name=?", gradingName);
    }

    public static String getCementAlkaliFile(String name) throws SQLArgumentException, SQLException {
        return getString("SELECT alkali_file FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?", name);
    }

    public static String getFlyAshAlkaliFile(String name) throws SQLArgumentException, SQLException {
        return getString("SELECT alkali_file FROM " + Constants.FLY_ASH_TABLE_NAME + " WHERE name=?", name);
    }

    public static String getSlagCharacteristicsFile(String name) throws SQLArgumentException, SQLException {
        return getString("SELECT characteristics_file FROM " + Constants.SLAG_TABLE_NAME + " WHERE name=?", name);
    }

    public static String getBulkModulusOfAggregateForUser(String display_name) throws SQLArgumentException, SQLException {
        if (display_name == null || display_name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "display_name", "The name is empty");
        }
        String sql = "SELECT bulk_modulus FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE display_name=?";
        String bulkModulus = null;

        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, display_name);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            bulkModulus = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return bulkModulus;
    }

    public static String getShearModulusOfAggregateForUser(String display_name) throws SQLArgumentException, SQLException {
        if (display_name == null || display_name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "display_name", "The name is empty");
        }
        String sql = "SELECT shear_modulus FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE display_name=?";
        String shearModulus = null;

        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, display_name);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            shearModulus = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return shearModulus;
    }

        public static String getConductivityOfAggregateForUser(String display_name) throws SQLArgumentException, SQLException {
        if (display_name == null || display_name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "display_name", "The name is empty");
        }
        String sql = "SELECT conductivity FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE display_name=?";
        String aggConductivity = null;

        Connection connection = getConnection();
        PreparedStatement pstmt;
        pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, display_name);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            aggConductivity = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return aggConductivity;
    }

    private static byte[] getDBFileDataForType(String name, String type) throws SQLArgumentException, DBFileException, SQLException {
        if (type == null || type.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The type is empty");
        }
        byte[] data = getBLOB("SELECT data FROM " + Constants.DB_FILE_TABLE_NAME + " WHERE name=? AND type='" + type + "'", name);
        if (data == null || data.length == 0) {
            throw new DBFileException(Constants.NO_DATA_FOR_THIS_NAME, type, "The data for \"" + name + "\" of type \"" + type + "\" is empty.");
        }
        return getBLOB("SELECT data FROM " + Constants.DB_FILE_TABLE_NAME + " WHERE name=? AND type='" + type + "'", name);
    }

    private static String getDBFileDataTextForType(String name, String type) throws SQLArgumentException, DBFileException, SQLException {
        return new String(getDBFileDataForType(name, type));
    }

    public static String getAlkaliCharacteristicsData(String name) throws SQLArgumentException, DBFileException, SQLException {
        return getDBFileDataTextForType(name, Constants.ALKALI_CHARACTERISTICS_TYPE);
    }

    public static String getSlagCharacteristicsData(String name) throws SQLArgumentException, DBFileException, SQLException {
        return getDBFileDataTextForType(name, Constants.SLAG_CHARACTERISTICS_TYPE);
    }

    public static String getParameterFileData(String name) throws SQLArgumentException, DBFileException, SQLException {
        return getDBFileDataTextForType(name, Constants.PARAMETER_FILE_TYPE);
    }

    public static String getCalorimetryFileData(String name) throws SQLArgumentException, DBFileException, SQLException {
        return getDBFileDataTextForType(name, Constants.CALORIMETRY_FILE_TYPE);
    }

    public static String getChemicalShrinkageFileData(String name) throws SQLArgumentException, DBFileException, SQLException {
        return getDBFileDataTextForType(name, Constants.CHEMICAL_SHRINKAGE_FILE_TYPE);
    }

    public static String getTimingOutputFileData(String name) throws SQLArgumentException, DBFileException, SQLException {
        return getDBFileDataTextForType(name, Constants.TIMING_OUTPUT_FILE_TYPE);
    }

    public static byte[] getPSDData(String name) throws SQLArgumentException, DBFileException, SQLException {
        return getDBFileDataForType(name, Constants.PSD_TYPE);
    }

    public static String getPSDText(String name) throws SQLArgumentException, DBFileException, SQLException {
        return getDBFileDataTextForType(name, Constants.PSD_TYPE);
    }

    public static String getCementPSD(String name) throws SQLArgumentException, SQLException {
        return getString("SELECT psd FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?", name);
    }

    public static List<String> getAlkaliCharacteristicsFilesNames() throws DBFileException, SQLArgumentException, SQLException {
        List<String> names = getNamesOfType(Constants.ALKALI_CHARACTERISTICS_TYPE);
        if (names == null || names.size() == 0) {
            throw new DBFileException(Constants.NO_DATA_OF_THIS_TYPE, Constants.ALKALI_CHARACTERISTICS_TYPE, "No alkali characteristics file has been found in the database.");
        }
        return names;
    }

    public static List<String> getSlagCharacteristicsFilesNames() throws DBFileException, SQLArgumentException, SQLException {
        List<String> names = getNamesOfType(Constants.SLAG_CHARACTERISTICS_TYPE);
        if (names == null || names.size() == 0) {
            throw new DBFileException(Constants.NO_DATA_OF_THIS_TYPE, Constants.SLAG_CHARACTERISTICS_TYPE, "No slag characteristics file has been found in the database.");
        }
        return names;
    }

    public static List<String> getParameterFilesNames() throws DBFileException, SQLArgumentException, SQLException {
        List<String> names = getNamesOfType(Constants.PARAMETER_FILE_TYPE);
        if (names == null || names.size() == 0) {
            throw new DBFileException(Constants.NO_DATA_OF_THIS_TYPE, Constants.PARAMETER_FILE_TYPE, "No parameters file has been found in the database.");
        }
        return names;
    }

    public static List<String> getChemicalShrinkageFilesNames() throws SQLArgumentException, DBFileException, SQLException {
        List<String> names = getNamesOfType(Constants.CHEMICAL_SHRINKAGE_FILE_TYPE);
        if (names == null || names.size() == 0) {
            throw new DBFileException(Constants.NO_DATA_OF_THIS_TYPE, Constants.CHEMICAL_SHRINKAGE_FILE_TYPE, "No chemical file has been found in the database.");
        }
        return names;
    }

    public static List<String> getCalorimetryFilesNames() throws SQLArgumentException, DBFileException, SQLException {
        List<String> names = getNamesOfType(Constants.CALORIMETRY_FILE_TYPE);
        if (names == null || names.size() == 0) {
            throw new DBFileException(Constants.NO_DATA_OF_THIS_TYPE, Constants.CALORIMETRY_FILE_TYPE, "No calorimetry file has been found in the database.");
        }
        return names;
    }

    public static List<String> getTimingOutputFilesNames() throws SQLArgumentException, DBFileException, SQLException {
        List<String> names = getNamesOfType(Constants.TIMING_OUTPUT_FILE_TYPE);
        if (names == null || names.size() == 0) {
            throw new DBFileException(Constants.NO_DATA_OF_THIS_TYPE, Constants.TIMING_OUTPUT_FILE_TYPE, "No timing output file has been found in the database.");
        }
        return names;
    }

    public static List<String> getPSDFilesNames() throws SQLArgumentException, DBFileException, SQLException {
        List<String> names = getNamesOfType(Constants.PSD_TYPE);
        if (names == null || names.size() == 0) {
            throw new DBFileException(Constants.NO_DATA_OF_THIS_TYPE, Constants.PSD_TYPE, "No psd has been found in the database.");
        }
        return names;
    }

    public static List<String> getDBFilesNames() throws SQLArgumentException, DBFileException, SQLException {
        List<String> names = getNamesInTable(Constants.DB_FILE_TABLE_NAME, "type");
        if (names == null || names.size() == 0) {
            throw new DBFileException(Constants.NO_DATA_OF_THIS_TYPE, "No cement data file has been found in the database.");
        }
        return names;
    }

    static private Cement cementFromResultSet(ResultSet rs) throws SQLException {
        Cement cement = new Cement();
        cement.setName(rs.getString("name"));
        cement.setPsd(rs.getString("psd"));
        cement.setPfc(rs.getBytes("pfc"));
        cement.setGif(rs.getBytes("gif"));
        cement.setLegend_gif(rs.getBytes("legend_gif"));
        cement.setSil(rs.getBytes("sil"));
        cement.setC3s(rs.getBytes("c3s"));
        cement.setC4f(rs.getBytes("c4f"));
        cement.setC3a(rs.getBytes("c3a"));
        cement.setN2o(rs.getBytes("n2o"));
        cement.setK2o(rs.getBytes("k2o"));
        cement.setAlu(rs.getBytes("alu"));
        cement.setDihyd(rs.getDouble("dihyd"));
        cement.setHemihyd(rs.getDouble("hemihyd"));
        cement.setAnhyd(rs.getDouble("anhyd"));
        cement.setTxt(rs.getBytes("txt"));
        cement.setXrd(rs.getBytes("xrd"));
        cement.setInf(rs.getBytes("inf"));
        cement.setAlkaliFile(rs.getString("alkali_file"));

        return cement;
    }

    public static Cement loadCement(String cementName) throws SQLException, SQLArgumentException {
        if (cementName == null || cementName.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The cement name is empty");
        }
        Cement cement = new Cement();

        Connection connection = getConnection();
        String sql = "SELECT * FROM " + Constants.CEMENT_TABLE_NAME + " WHERE name=?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, cementName);
        ResultSet rs = pstmt.executeQuery();
        if (rs.next()) {
            cement = cementFromResultSet(rs);
        }
        rs.close();
        pstmt.close();
        connection.close();

        String path = Vcctl.getImageDirectory() + cementName + ".gif";
        File f = new File(path);
        if (!(f.exists())) {
            if (cement.getGif() != null) {
                boolean result = ServerFile.saveToFile(path, cement.getGif());
            } else {
                byte[] imgdata = ServerFile.readBinaryFile(path,"NoImage.gif");
                path += cementName + ".gif";
                boolean result = ServerFile.saveToFile(path,imgdata);
            }
        }

        return cement;
    }

    public static void saveCement(Cement cement) throws SQLException {
        Connection connection = getConnection();
        String sqlcmd = "UPDATE " + Constants.CEMENT_TABLE_NAME + " SET psd=?, pfc=?, gif=?, legend_gif=?, " +
                "sil=?, c3s=?, c4f=?, c3a=?, n2o=?, k2o=?, alu=?, dihyd=?, hemihyd=?, anhyd=?, txt=?, " +
                "xrd=?, inf=?, alkali_file=? WHERE name=?";
        PreparedStatement pstmt = connection.prepareStatement(sqlcmd);

        byte[] imgdata;
        if (cement.getGif() != null) {
            imgdata = cement.getGif();
        } else {
            String path = Vcctl.getImageDirectory();
            imgdata = ServerFile.readBinaryFile(path,"NoImage.gif");
        }
        pstmt.setString(1, cement.getPsd());
        pstmt.setBytes(2, cement.getPfc());
        pstmt.setBytes(3, imgdata);
        pstmt.setBytes(4, cement.getLegend_gif());
        pstmt.setBytes(5, cement.getSil());
        pstmt.setBytes(6, cement.getC3s());
        pstmt.setBytes(7, cement.getC4f());
        pstmt.setBytes(8, cement.getC3a());
        pstmt.setBytes(9, cement.getN2o());
        pstmt.setBytes(10, cement.getK2o());
        pstmt.setBytes(11, cement.getAlu());
        pstmt.setDouble(12, cement.getDihyd());
        pstmt.setDouble(13, cement.getHemihyd());
        pstmt.setDouble(14, cement.getAnhyd());
        pstmt.setBytes(15, cement.getTxt());
        pstmt.setBytes(16, cement.getXrd());
        pstmt.setBytes(17, cement.getInf());
        pstmt.setString(18, cement.getAlkaliFile());
        pstmt.setString(19, cement.getName());

        pstmt.executeUpdate();

        pstmt.close();
        connection.close();
    }

    public static void saveCementAs(Cement cement) throws SQLException {
        Connection connection = getConnection();
        String sqlcmd = "INSERT INTO " + Constants.CEMENT_TABLE_NAME + " (name, psd, pfc, " +
                "gif, legend_gif, sil, c3s, c4f, c3a, n2o, k2o, alu, dihyd, hemihyd, anhyd, " +
                "txt, xrd, inf, alkali_file) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)";
        PreparedStatement pstmt = connection.prepareStatement(sqlcmd);

        byte[] imgdata;
        if (cement.getGif() != null) {
            imgdata = cement.getGif();
        } else {
            String path = Vcctl.getImageDirectory();
            imgdata = ServerFile.readBinaryFile(path,"NoImage.gif");
        }

        pstmt.setString(1, cement.getName());
        pstmt.setString(2, cement.getPsd());
        pstmt.setBytes(3, cement.getPfc());
        pstmt.setBytes(4, imgdata);
        pstmt.setBytes(5, cement.getLegend_gif());
        pstmt.setBytes(6, cement.getSil());
        pstmt.setBytes(7, cement.getC3s());
        pstmt.setBytes(8, cement.getC4f());
        pstmt.setBytes(9, cement.getC3a());
        pstmt.setBytes(10, cement.getN2o());
        pstmt.setBytes(11, cement.getK2o());
        pstmt.setBytes(12, cement.getAlu());
        pstmt.setDouble(13, cement.getDihyd());
        pstmt.setDouble(14, cement.getHemihyd());
        pstmt.setDouble(15, cement.getAnhyd());
        pstmt.setBytes(16, cement.getTxt());
        pstmt.setBytes(17, cement.getXrd());
        pstmt.setBytes(18, cement.getInf());
        pstmt.setString(19, cement.getAlkaliFile());

        pstmt.executeUpdate();

        pstmt.close();
        connection.close();

        String path = Vcctl.getImageDirectory() + cement.getName() + ".gif";
        boolean result = ServerFile.saveToFile(path, imgdata);
    }

    public static void deleteCement(Cement cement) throws SQLException {
        deleteEntryOfNameFromTable(Constants.CEMENT_TABLE_NAME, cement.getName());
    }

    static private DBFile dbFileFromResultSet(ResultSet rs) throws SQLException {
        String type = rs.getString("type");
        type = type.trim();
        DBFile dbf = new DBFile(type);
        dbf.setName(rs.getString("name"));
        dbf.setData(rs.getBytes("data"));
        dbf.setInf(rs.getBytes("inf"));

        return dbf;
    }

    public static DBFile loadDBFile(String name) throws SQLException, SQLArgumentException {
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The cement name is empty");
        }
        DBFile dbf = null;
        Connection connection = getConnection();

        String sql = "SELECT * FROM " + Constants.DB_FILE_TABLE_NAME + " WHERE name=?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        ResultSet rs = pstmt.executeQuery();
        if (rs.next()) {
            dbf = dbFileFromResultSet(rs);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return dbf;
    }

    public static void saveDBFile(DBFile dbFile) throws SQLArgumentException, SQLDuplicatedKeyException, SQLException {
        String name = dbFile.getName();
        String type = dbFile.getType();
        Connection connection = getConnection();
        PreparedStatement pstmt;

        if (dbFileExists(name)) {
            String sql = "UPDATE " + Constants.DB_FILE_TABLE_NAME + " SET type=?, data=?, inf=? WHERE name=?";
            pstmt = connection.prepareStatement(sql);
            pstmt.setString(1, type);
            pstmt.setBytes(2, dbFile.getData());
            pstmt.setBytes(3, dbFile.getInf());
            pstmt.setString(4, name);
        } else {
            String sql = "INSERT INTO " + Constants.DB_FILE_TABLE_NAME + " (name, type, data, inf) VALUES (?,?,?,?)";

            pstmt = connection.prepareStatement(sql);
            pstmt.setString(1, name);
            pstmt.setString(2, type);
            pstmt.setBytes(3, dbFile.getData());
            pstmt.setBytes(4, dbFile.getInf());
        }

        pstmt.executeUpdate();

        pstmt.close();
        connection.close();
    }

    public static void saveDBFileAs(DBFile dbFile) throws SQLArgumentException, SQLDuplicatedKeyException, SQLException {
        String name = dbFile.getName();
        String type = dbFile.getType();
        byte[] dbdata = dbFile.getData();
        byte[] dbinf = dbFile.getInf();
        Connection connection = getConnection();

        String sql = "INSERT INTO " + Constants.DB_FILE_TABLE_NAME + " (name, type, data, inf) VALUES (?,?,?,?)";

        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        pstmt.setString(2, type);
        pstmt.setBytes(3, dbdata);
        pstmt.setBytes(4, dbinf);


        pstmt.executeUpdate();

        pstmt.close();
        connection.close();
    }

    public static void deleteDBFile(DBFile dbFile) throws SQLException {
        deleteEntryOfNameFromTable(Constants.DB_FILE_TABLE_NAME, dbFile.getName());
    }

    static private Slag slagFromResultSet(ResultSet rs) throws SQLException, DBFileException {
        Slag s = new Slag();
        s.setName(rs.getString("name"));
        s.setSpecific_gravity(rs.getDouble("sg"));
        s.setPsd(rs.getString("psd"));
        s.setMolecular_mass(rs.getDouble("mm"));
        s.setCasi_mol_ratio(rs.getDouble("csmr"));
        s.setSi_per_mole(rs.getDouble("sipm"));
        s.setBase_slag_reactivity(rs.getDouble("reactivity"));
        s.setHp_molecular_mass(rs.getDouble("hp_mm"));
        s.setHp_density(rs.getDouble("hp_den"));
        s.setHp_casi_mol_ratio(rs.getDouble("hp_csmr"));
        s.setHp_h2osi_mol_ratio(rs.getDouble("hp_hsmr"));
        s.setC3a_per_mole(rs.getDouble("c3apm"));
        s.setDescription(rs.getString("descr"));

        return s;
    }

    public static Slag loadSlag(String name) throws SQLException, SQLArgumentException, DBFileException {
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The cement name is empty");
        }
        Slag s = null;
        Connection connection = getConnection();

        String sql = "SELECT * FROM " + Constants.SLAG_TABLE_NAME + " WHERE name=?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        ResultSet rs = pstmt.executeQuery();
        if (rs.next()) {
            s = slagFromResultSet(rs);
        }
        rs.close();
        pstmt.close();
        connection.close();

        return s;
    }

    public static void saveSlag(Slag slag) throws SQLException {
        Connection connection = getConnection();

        String sql = "UPDATE " + Constants.SLAG_TABLE_NAME + " SET sg=?, psd=?, mm=?, csmr=?, " +
                "sipm=?, reactivity=?, hp_mm=?, hp_den=?, hp_csmr=?, hp_hsmr=?, c3apm=?, descr=? " +
                "WHERE name=?";

        PreparedStatement pstmt = connection.prepareStatement(sql);

        pstmt.setDouble(1, slag.getSpecific_gravity());
        pstmt.setString(2, slag.getPsd());
        pstmt.setDouble(3, slag.getMolecular_mass());
        pstmt.setDouble(4, slag.getCasi_mol_ratio());
        pstmt.setDouble(5, slag.getSi_per_mole());
        pstmt.setDouble(6, slag.getBase_slag_reactivity());
        pstmt.setDouble(7, slag.getHp_molecular_mass());
        pstmt.setDouble(8, slag.getHp_density());
        pstmt.setDouble(9, slag.getHp_casi_mol_ratio());
        pstmt.setDouble(10, slag.getHp_h2osi_mol_ratio());
        pstmt.setDouble(11, slag.getC3a_per_mole());
        pstmt.setString(12, slag.getDescription());
        pstmt.setString(13, slag.getName());

        pstmt.executeUpdate();

        pstmt.close();
        connection.close();
    }

    public static void saveSlagAs(Slag slag) throws SQLException {
        Connection connection = getConnection();

        String sql = "INSERT INTO " + Constants.SLAG_TABLE_NAME + " (name, sg, psd, mm, csmr, " +
                "sipm, reactivity, hp_mm, hp_den, hp_csmr, hp_hsmr, c3apm, descr) " +
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)";

        PreparedStatement pstmt = connection.prepareStatement(sql);

        pstmt.setString(1, slag.getName());
        pstmt.setDouble(2, slag.getSpecific_gravity());
        pstmt.setString(3, slag.getPsd());
        pstmt.setDouble(4, slag.getMolecular_mass());
        pstmt.setDouble(5, slag.getCasi_mol_ratio());
        pstmt.setDouble(6, slag.getSi_per_mole());
        pstmt.setDouble(7, slag.getBase_slag_reactivity());
        pstmt.setDouble(8, slag.getHp_molecular_mass());
        pstmt.setDouble(9, slag.getHp_density());
        pstmt.setDouble(10, slag.getHp_casi_mol_ratio());
        pstmt.setDouble(11, slag.getHp_h2osi_mol_ratio());
        pstmt.setDouble(12, slag.getC3a_per_mole());
        pstmt.setString(13, slag.getDescription());

        pstmt.executeUpdate();

        pstmt.close();
        connection.close();
    }

    public static void deleteSlag(Slag slag) throws SQLException {
        deleteEntryOfNameFromTable(Constants.SLAG_TABLE_NAME, slag.getName());
    }

    static private FlyAsh flyAshFromResultSet(ResultSet rs) throws SQLException, DBFileException {
        FlyAsh fla = new FlyAsh();
        fla.setName(rs.getString("name"));
        fla.setSpecific_gravity(rs.getDouble("sg"));
        fla.setPsd(rs.getString("psd"));
        fla.setDistribute_phases_by(rs.getInt("distribute_by"));
        fla.setAluminosilicate_glass_fraction(rs.getDouble("ag"));
        fla.setCalcium_aluminum_disilicate_fraction(rs.getDouble("cad"));
        fla.setTricalcium_aluminate_fraction(rs.getDouble("ta"));
        fla.setCalcium_chloride_fraction(rs.getDouble("cc"));
        fla.setSilica_fraction(rs.getDouble("sil"));
        fla.setAnhydrite_fraction(rs.getDouble("anh"));
        fla.setDescription(rs.getString("descr"));

        return fla;
    }

    public static FlyAsh loadFlyAsh(String name) throws SQLException, SQLArgumentException, DBFileException {
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The cement name is empty");
        }
        Connection connection = getConnection();
        FlyAsh fla = null;

        String sql = "SELECT * FROM " + Constants.FLY_ASH_TABLE_NAME + " WHERE name=?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        ResultSet rs = pstmt.executeQuery();
        if (rs.next()) {
            fla = flyAshFromResultSet(rs);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return fla;
    }

    public static void saveFlyAsh(FlyAsh flyAsh) throws SQLException {
        Connection connection = getConnection();

        String sql = "UPDATE " + Constants.FLY_ASH_TABLE_NAME + " SET sg=?, psd=?, distribute_by=?, ag=?, " +
                "cad=?, ta=?, cc=?, sil=?, anh=?, descr=? WHERE name=?";

        PreparedStatement pstmt = connection.prepareStatement(sql);

        pstmt.setDouble(1, flyAsh.getSpecific_gravity());
        pstmt.setString(2, flyAsh.getPsd());
        pstmt.setInt(3, flyAsh.getDistribute_phases_by());
        pstmt.setDouble(4, flyAsh.getAluminosilicate_glass_fraction());
        pstmt.setDouble(5, flyAsh.getCalcium_aluminum_disilicate_fraction());
        pstmt.setDouble(6, flyAsh.getTricalcium_aluminate_fraction());
        pstmt.setDouble(7, flyAsh.getCalcium_chloride_fraction());
        pstmt.setDouble(8, flyAsh.getSilica_fraction());
        pstmt.setDouble(9, flyAsh.getAnhydrite_fraction());
        pstmt.setString(10, flyAsh.getDescription());
        pstmt.setString(11, flyAsh.getName());

        pstmt.executeUpdate();

        pstmt.close();
        connection.close();
    }

    public static void saveFlyAshAs(FlyAsh flyAsh) throws SQLException {
        Connection connection = getConnection();

        String sql = "INSERT INTO " + Constants.FLY_ASH_TABLE_NAME + " (name, sg, psd, " +
                "distribute_by, ag, cad, ta, cc, sil, anh, descr) VALUES (?,?,?,?,?,?,?,?,?,?,?)";

        PreparedStatement pstmt = connection.prepareStatement(sql);

        pstmt.setString(1, flyAsh.getName());
        pstmt.setDouble(2, flyAsh.getSpecific_gravity());
        pstmt.setString(3, flyAsh.getPsd());
        pstmt.setInt(4, flyAsh.getDistribute_phases_by());
        pstmt.setDouble(5, flyAsh.getAluminosilicate_glass_fraction());
        pstmt.setDouble(6, flyAsh.getCalcium_aluminum_disilicate_fraction());
        pstmt.setDouble(7, flyAsh.getTricalcium_aluminate_fraction());
        pstmt.setDouble(8, flyAsh.getCalcium_chloride_fraction());
        pstmt.setDouble(9, flyAsh.getSilica_fraction());
        pstmt.setDouble(10, flyAsh.getAnhydrite_fraction());
        pstmt.setString(11, flyAsh.getDescription());

        pstmt.executeUpdate();

        pstmt.close();
        connection.close();
    }

    public static void deleteFlyAsh(FlyAsh flyAsh) throws SQLException {
        deleteEntryOfNameFromTable(Constants.FLY_ASH_TABLE_NAME, flyAsh.getName());
    }

    static private Grading gradingFromResultSet(ResultSet rs) throws SQLException {
        Grading grading = new Grading();
        grading.setName(rs.getString("name"));
        grading.setType(rs.getInt("type"));
        grading.setGrading(rs.getBytes("txt"));

        return grading;
    }

    public static Grading loadGrading(String name) throws SQLException, SQLArgumentException {
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The cement name is empty");
        }
        Grading grading = null;
        Connection connection = getConnection();

        String sql = "SELECT * FROM " + Constants.GRADING_TABLE_NAME + " WHERE name=?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        ResultSet rs = pstmt.executeQuery();
        if (rs.next()) {
            grading = gradingFromResultSet(rs);
        }
        rs.close();
        pstmt.close();
        connection.close();

        return grading;
    }

    public static void saveGrading(Grading grading) throws SQLDuplicatedKeyException, SQLArgumentException, SQLException {
        String name = grading.getName();
        if (!CementDatabase.isUniqueGradingName(name)) {
            throw new SQLDuplicatedKeyException(Constants.GRADING_TABLE_NAME,
                    name,
                    "There already is a grading called '" + name + "' in the database.");
        }
        Connection connection = getConnection();

        String sql = "INSERT INTO " + Constants.GRADING_TABLE_NAME + " (name, aggregate_type, grading, max_diameter) VALUES (?,?,?,?)";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        pstmt.setInt(2, grading.getType());
        pstmt.setBytes(3, grading.getGrading());
        pstmt.setDouble(4, grading.getMax_diameter());

        pstmt.executeUpdate();

        pstmt.close();
        connection.close();
    }

    static private InertFiller inertFillerFromResultSet(ResultSet rs) throws SQLException, DBFileException {
        InertFiller fill = new InertFiller();
        fill.setName(rs.getString("name"));
        fill.setSpecific_gravity(rs.getDouble("sg"));
        fill.setPsd(rs.getString("psd"));
        fill.setDescription(rs.getString("descr"));

        return fill;
    }

    public static InertFiller loadInertFiller(String name) throws SQLException, SQLArgumentException, DBFileException {
        if (name == null || name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The cement name is empty");
        }
        InertFiller fill = null;
        Connection connection = getConnection();

        String sql = "SELECT * FROM " + Constants.INERT_FILLER_TABLE_NAME + " WHERE name=?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        ResultSet rs = pstmt.executeQuery();
        if (rs.next()) {
            fill = inertFillerFromResultSet(rs);
        }
        rs.close();
        pstmt.close();
        connection.close();

        return fill;
    }

    public static void saveInertFiller(InertFiller inertFiller) throws SQLException {
        Connection connection = getConnection();

        String sql = "UPDATE " + Constants.INERT_FILLER_TABLE_NAME + " SET sg=?, psd=?, descr=? WHERE name=?";
        PreparedStatement pstmt = connection.prepareStatement(sql);

        pstmt.setDouble(1, inertFiller.getSpecific_gravity());
        pstmt.setString(2, inertFiller.getPsd());
        pstmt.setString(3, inertFiller.getDescription());
        pstmt.setString(4, inertFiller.getName());

        pstmt.executeUpdate();

        pstmt.close();
        connection.close();
    }

    public static void saveInertFillerAs(InertFiller inertFiller) throws SQLException {
        Connection connection = getConnection();

        String sql = "INSERT INTO " + Constants.INERT_FILLER_TABLE_NAME + " (name, sg, psd, " +
                "descr) VALUES (?,?,?,?)";
        PreparedStatement pstmt = connection.prepareStatement(sql);

        pstmt.setString(1, inertFiller.getName());
        pstmt.setDouble(2, inertFiller.getSpecific_gravity());
        pstmt.setString(3, inertFiller.getPsd());
        pstmt.setString(4, inertFiller.getDescription());

        pstmt.executeUpdate();

        pstmt.close();
        connection.close();
    }

    public static void deleteInertFiller(InertFiller inertFiller) throws SQLException {
        deleteEntryOfNameFromTable(Constants.INERT_FILLER_TABLE_NAME, inertFiller.getName());
    }

    static private Aggregate aggregateFromResultSet(ResultSet rs) throws SQLException {
        Aggregate aggregate = new Aggregate();
        aggregate.setName(rs.getString("name"));
        aggregate.setDisplay_name(rs.getString("display_name"));
        aggregate.setType(rs.getInt("aggregate_type"));
        aggregate.setSpecific_gravity(rs.getDouble("specific_gravity"));
        aggregate.setImage(rs.getBytes("gif"));
        aggregate.setTxt(rs.getBytes("txt"));
        aggregate.setInf(rs.getBytes("inf"));
        aggregate.setBulk_modulus(rs.getDouble("bulk_modulus"));
        aggregate.setShear_modulus(rs.getDouble("shear_modulus"));
        aggregate.setConductivity(rs.getDouble("conductivity"));
        aggregate.setShape_stats(rs.getBytes("shape_stats"));
        return aggregate;
    }

    public static Aggregate loadAggregate(String display_name) throws SQLException, SQLArgumentException {
        if (display_name == null || display_name.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "name", "The cement name is empty");
        }
        Aggregate aggregate = null;
        Connection connection = CementDatabase.getConnection();

        String sql = "SELECT * FROM " + Constants.AGGREGATE_TABLE_NAME + " WHERE display_name=?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, display_name);
        ResultSet rs = pstmt.executeQuery();
        if (rs.next()) {
            aggregate = aggregateFromResultSet(rs);
        }
        rs.close();
        pstmt.close();
        connection.close();
        String aggname = aggregate.getName();

        String path = Vcctl.getImageDirectory() + aggname + ".gif";
        File f = new File(path);
        if (!(f.exists())) {
            if (aggregate.getImage() != null) {
                boolean result = ServerFile.saveToFile(path, aggregate.getImage());
            } else {
                path = Vcctl.getImageDirectory();
                byte[] imgdata = ServerFile.readBinaryFile(path,"NoImage.gif");
                path += aggname + ".gif";
                boolean result = ServerFile.saveToFile(path,imgdata);
            }
        }
        return aggregate;
    }

    public static void saveAggregate(Aggregate aggregate) throws SQLDuplicatedKeyException, SQLArgumentException, SQLException {
        String display_name = aggregate.getDisplay_name();
        Connection connection = CementDatabase.getConnection();

        String sql = "UPDATE " + Constants.AGGREGATE_TABLE_NAME + " SET name=?, gif=?, txt=?, inf=?, bulk_modulus=?, shear_modulus=?, conductivity=?, specific_gravity=?, shape_stats=? WHERE display_name=?";
        PreparedStatement pstmt = connection.prepareStatement(sql);

        // Everything temporary from here to save gif files

        // String aggdir = Vcctl.getAggregateDirectory() + name;
        // aggdir = aggdir + File.separator;
        // String gifstring = name + ".gif";
        // String path = aggdir + gifstring;
        // byte[] bgif;
        // File f = new File(path);
        // if (f.exists()) {
        //     bgif = ServerFile.readBinaryFile(aggdir, gifstring);
        // } else {
        //     path = Vcctl.getImageDirectory();
        //     bgif = ServerFile.readBinaryFile(path,"NoImage.gif");
        // }

        // pstmt.setBytes(1, bgif);

        // to here

        // Everything temporary from here to save shape_stats files
        // String sststring = name + ".sst";
        // path = aggdir + sststring;
        // String sshapestats = "";
        // byte[] bshapestats;
        // f = new File(path);
        // if (f.exists()) {
        //     sshapestats = ServerFile.readTextFile(aggdir, sststring);
        // }
        // bshapestats = sshapestats.getBytes();
        // aggregate.setShape_stats(bshapestats);
        // aggregate.setShapestatsString(sshapestats);

        // to here

        // Everything temporary from here to save shape_stats files
        // String infostring = name + "-info.dat";
        // path = aggdir + infostring;
        // String sinfo = "";
        // byte[] binfo;
        // f = new File(path);
        // if (f.exists()) {
        //     sinfo = ServerFile.readTextFile(aggdir, infostring);
        // }
        // binfo = sinfo.getBytes();
        // aggregate.setInf(binfo);
        // aggregate.setInfString(sinfo);

        // to here
        // pstmt.setBytes(1, aggregate.getImage());
        
        pstmt.setString(1, aggregate.getName());
        pstmt.setBytes(2, aggregate.getImage());
        pstmt.setBytes(3, aggregate.getTxt());
        pstmt.setBytes(4, aggregate.getInf());
        pstmt.setDouble(5, aggregate.getBulk_modulus());
        pstmt.setDouble(6, aggregate.getShear_modulus());
        pstmt.setDouble(7, aggregate.getConductivity());
        pstmt.setDouble(8, aggregate.getSpecific_gravity());
        pstmt.setBytes(9, aggregate.getShape_stats());
        pstmt.setString(10, display_name);

        pstmt.executeUpdate();

        pstmt.close();
        connection.close();

        // String path = Vcctl.getImageDirectory() + name + ".gif";
        // boolean result = ServerFile.saveToFile(path, bgif);
    }

    public static void saveAggregateAs(Aggregate aggregate) throws SQLDuplicatedKeyException, SQLArgumentException, SQLException {
        String display_name = aggregate.getDisplay_name();
        String name = aggregate.getName();
        Connection connection = CementDatabase.getConnection();

        String sql = "INSERT INTO " + Constants.AGGREGATE_TABLE_NAME + " (name, aggregate_type, gif, txt, inf, bulk_modulus, " +
                "shear_modulus, conductivity, specific_gravity, shape_stats, display_name) VALUES (?,?,?,?,?,?,?,?,?,?,?)";
        PreparedStatement pstmt = connection.prepareStatement(sql);

        // String aggdir = Vcctl.getAggregateDirectory() + name;
        // aggdir = aggdir + File.separator;
        // String gifstring = name + ".gif";
        // String path = aggdir + gifstring;
        // byte[] bgif;
        // File f = new File(path);
        // if (f.exists()) {
        //     bgif = ServerFile.readBinaryFile(aggdir, gifstring);
        // } else {
        //     path = Vcctl.getImageDirectory();
        //     bgif = ServerFile.readBinaryFile(path,"NoImage.gif");
        // }

        // Everything temporary from here to save shape_stats files
        // String sststring = name + ".sst";
        // path = aggdir + sststring;
        // String sshapestats = "";
        // byte[] bshapestats;
        // f = new File(path);
        // if (f.exists()) {
        //     sshapestats = ServerFile.readTextFile(aggdir, sststring);
        // }
        // bshapestats = sshapestats.getBytes();

        pstmt.setString(1, name);
        pstmt.setInt(2, aggregate.getType());
        pstmt.setBytes(3, aggregate.getImage());
        pstmt.setBytes(4, aggregate.getTxt());
        pstmt.setBytes(5, aggregate.getInf());
        pstmt.setDouble(6, aggregate.getBulk_modulus());
        pstmt.setDouble(7, aggregate.getShear_modulus());
        pstmt.setDouble(8, aggregate.getConductivity());
        pstmt.setDouble(9, aggregate.getSpecific_gravity());
        pstmt.setBytes(10, aggregate.getShape_stats());
        pstmt.setString(11, display_name);

        pstmt.executeUpdate();

        pstmt.close();
        connection.close();

        // String path = Vcctl.getImageDirectory() + name + ".gif";
        // boolean result = ServerFile.saveToFile(path, aggregate.getImage());
    }

    public static void deleteAggregate(Aggregate agg) throws SQLException {
        deleteEntryOfDisplayNameFromTable(Constants.AGGREGATE_TABLE_NAME, agg.getDisplay_name());
    }

    // The folllowing function is a generic getter for image data from the
    // database.  Currently, only cements and aggregates have images.
    public static byte[] getGif(String materialType, String name) throws SQLException, SQLArgumentException {
        if (materialType == null || materialType.equalsIgnoreCase("")) {
            throw new SQLArgumentException(Constants.EMPTY_ARGUMENT, "type", "The type is empty");
        }

        byte[] imgData = null;
        Connection connection = getConnection();
        PreparedStatement pstmt;
        String sql = "SELECT gif FROM " + materialType + " WHERE name = ?";
        ResultSet rs = null;
        boolean retval = true;
        pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, name);
        rs = pstmt.executeQuery();
        int row_count = 0;
        while (rs.next()) {
            imgData = rs.getBytes("gif");
        }
        rs.close();
        pstmt.close();
        connection.close();

        return imgData;
    }

    public static boolean writeGifToFile(String materialType, String name) {

        boolean result = false;
        try {
            String path = Vcctl.getImageDirectory() + name + ".gif";
            byte[] imgdata = getGif(materialType,name);
            result = ServerFile.saveToFile(path, imgdata);
        } catch (SQLException e1) {
            e1.printStackTrace();
        } catch (SQLArgumentException e2) {
            e2.printStackTrace();
        }
        return result;
    }
}
