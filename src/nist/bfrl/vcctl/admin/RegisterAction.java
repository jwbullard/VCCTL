/*
 * RegisterAction.java
 *
 * Created on August 21, 2007, 3:34 AM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.admin;

import java.io.*;
import java.sql.SQLException;
import java.util.Map;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import nist.bfrl.vcctl.database.UserDatabase;
import nist.bfrl.vcctl.application.Vcctl;
import nist.bfrl.vcctl.util.Util;
import org.apache.struts.action.Action;
import org.apache.struts.action.ActionForm;
import org.apache.struts.action.ActionForward;
import org.apache.struts.action.ActionMapping;

/**
 *
 * @author mscialom
 */
public class RegisterAction extends Action {
    
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws IOException {
        
        Map pm = request.getParameterMap();
        RegisterForm registerForm = (RegisterForm)form;
        HttpSession session = request.getSession();
        
        String userName = registerForm.getUserName();
        String password = registerForm.getPassword();
        String email = registerForm.getEmail();
        
        
        try {
            if (pm.containsKey("action")) {
                String[] actions = (String[])pm.get("action");
                String action = actions[0];
                if (action.equalsIgnoreCase("check_username")) {
                    if (UserDatabase.userExist(userName)) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("name_alreadyTaken");
                        out.flush();
                        return null;
                    }
                } else if (action.equalsIgnoreCase("check_email")) {
                    if (UserDatabase.emailExist(email)) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("email_alreadyTaken");
                        out.flush();
                        return null;
                    }
                }
            } else {
                
                if (!UserDatabase.userExist(userName) && !UserDatabase.emailExist(email)) {
                    UserDatabase.createUser(userName,password,email);
                    String sourceDirString = Vcctl.getDBDirectoryNoSep();
                    Vcctl.setUserName(userName);
                    String targetDirString = Vcctl.getDBDirectoryNoSep();
                    File sourceDir = new File(sourceDirString);
                    File targetDir = new File(targetDirString);
                    try {
                        Util.copyDirectory(sourceDir,targetDir);
                        return (mapping.findForward("success"));
                    } catch (IOException ex) {
                        String msg = ex.getMessage();
                        return (mapping.findForward("failure"));
                    }
                } else {
                    return (mapping.findForward("failure"));
                }
            }
        } catch (SQLException ex) {
            String msg = ex.getMessage();
            String smsg = ex.getSQLState();
            return (mapping.findForward("database_problem"));
        }
        return (mapping.findForward("failure"));
    }
    
}
