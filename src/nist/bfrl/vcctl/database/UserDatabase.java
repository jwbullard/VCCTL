/*
 * UserDatabase.java
 *
 * Created on July 27, 2007, 4:18 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.database;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.Util;
import nist.bfrl.vcctl.application.Vcctl;
import org.apache.derby.jdbc.EmbeddedDriver;

/**
 *
 * @author mscialom
 */
public class UserDatabase {
    
    /** Creates a new instance of UserDatabase */
    public UserDatabase() {
    }
    
    static protected Connection getConnection() throws SQLException {
        VCCTLDatabase.loadDriver();
        Connection cxn = null;
        // to do: allow the admin to change the password
        String url = "jdbc:derby:" + Vcctl.getDBDirectory() + "vcctl_user";
        cxn = DriverManager.getConnection(url);
        return cxn;
    }
    
    public static boolean userExist(String userName) throws SQLException {
        Connection connection = getConnection();
        String name = "";
        
        String sql = "SELECT name FROM " + Constants.USER_TABLE_NAME + " WHERE name = ?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, userName);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            name = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        if (!name.equalsIgnoreCase(""))
            return true;
        return false;
    }
    
    public static boolean emailExist(String email) throws SQLException {
        /* Disabling this function for now. Always return false */
        /*
        Connection connection = getConnection();
        String name = "";
        String sql = "SELECT email FROM " + Constants.USER_TABLE_NAME + " WHERE email = ?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, email);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            name = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        if (!name.equalsIgnoreCase(""))
            return true;
        */
        return false;
    }
    
    public static List<String> getUserNames() throws SQLException {
        Connection connection = getConnection();
        ArrayList<String> names = new ArrayList();
        String sql = "SELECT name FROM " + Constants.USER_TABLE_NAME;
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
    
    public static boolean checkForUser(String userName) throws SQLException {
        Connection connection = getConnection();
        String user = "";
        String sql = "SELECT name FROM " + Constants.USER_TABLE_NAME + " WHERE name = ?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, userName);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            user = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        if (!user.equalsIgnoreCase(""))
            return true;
        
        return false;
    }
    
    
    public static boolean checkPasswordForUser(String userName, String password) throws SQLException {
        Connection connection = getConnection();
        String pass = "";
        String sql = "SELECT password FROM " + Constants.USER_TABLE_NAME + " WHERE name = ?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, userName);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            pass = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        if (!pass.equalsIgnoreCase("") && pass.matches(password))
            return true;
        
        return false;
    }
    
    public static void sendUserNameAndPasswordToUserEmailAddress(String email) throws SQLException {
        Connection connection = getConnection();
        String password = "";
        String userName = "";
        String sql = "SELECT userName, password FROM " + Constants.USER_TABLE_NAME + " WHERE email = ?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, email);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            userName = rs.getString(1);
            password = rs.getString(2);
        }
        
        if (!userName.equalsIgnoreCase("") && !password.equalsIgnoreCase("")) {
            /* send user name and password */
        }
        
        rs.close();
        pstmt.close();
        connection.close();
    }
    
    public static String getUserEmail(String userName) throws SQLException {
        Connection connection = getConnection();
        String email = "";
        String sql = "SELECT email FROM " + Constants.USER_TABLE_NAME + " WHERE name = ?";
        PreparedStatement pstmt = connection.prepareStatement(sql);
        pstmt.setString(1, userName);
        ResultSet rs = pstmt.executeQuery();
        while (rs.next()) {
            email = rs.getString(1);
        }
        rs.close();
        pstmt.close();
        connection.close();
        return email;
    }
    
    public static boolean createUser(String userName, String password, String email) throws SQLException {
        boolean success = false;
        if (!userExist(userName) && !emailExist(email)) {
            String datetime = Util.currentDateTime();
            int retval = -1;
            String sql;
            sql = "INSERT INTO " + Constants.USER_TABLE_NAME + " (name, password, registration_date, email) VALUES(?,?,?,?)";
            
            Connection connection = getConnection();
            PreparedStatement pstmt = connection.prepareStatement(sql);
            pstmt.setString(1, userName);
            pstmt.setString(2, password);
            pstmt.setString(3, datetime);
            pstmt.setString(4, email);
            retval = pstmt.executeUpdate();
            success = (retval == 1);
            pstmt.close();
            connection.close();
        }
        
        return success;
    }
}
