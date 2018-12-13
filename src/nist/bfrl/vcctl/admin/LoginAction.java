/*
 * LoginAction.java
 *
 * Created on January 19, 2005, 3:19 PM
 */

package nist.bfrl.vcctl.admin;

import java.sql.SQLException;
import javax.servlet.http.*;
import nist.bfrl.vcctl.database.User;
import nist.bfrl.vcctl.database.UserDatabase;
import nist.bfrl.vcctl.database.VCCTLDatabase;
import org.apache.struts.action.*;

import java.io.File;
import java.io.IOException;
import nist.bfrl.vcctl.application.Vcctl;


/**
 *
 * @author tahall
 */
public final class LoginAction extends Action {
    
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {
        
        LoginForm loginForm = (LoginForm)form;
        HttpSession session = request.getSession();
        
        String userName = loginForm.getUserName();
        String password = loginForm.getPassword();
        boolean isUserInDatabase; // to see if the user is actually in the database;
        boolean loginSuccessful;
        try {
            
            isUserInDatabase = UserDatabase.checkForUser(userName);
            
            if(isUserInDatabase) {
               loginSuccessful = UserDatabase.checkPasswordForUser(userName, password);
            
               if (loginSuccessful) {
                    session.setAttribute("login", loginForm);
                
                    String vcctlroot = this.getServlet().getServletContext().getRealPath("/");
                    File rootdir = new File(vcctlroot+"/");
                    try {
                        vcctlroot = rootdir.getCanonicalPath();
                    } catch (IOException iox) {
                        throw new RuntimeException(iox);
                    }
                    Vcctl.setRootDir(vcctlroot);
                
                    /*
                     * Create a new user and start a new session
                     */
                    String email = UserDatabase.getUserEmail(userName);
                    User user = new User(userName, email);
                    session.setAttribute("user", user);
                    session.setAttribute("user_email", email);

                    /* Set the userName for this session */

                    Vcctl.setUserName(userName);

                    return (mapping.findForward("success"));

                } else {

                    ActionMessages errors = new ActionMessages();
                    // errors.add("email", new ActionMessage("invalid.email", email));
                    this.saveErrors(request, errors);
                
                    return (mapping.findForward("failure2"));
                }
            } else {// the user is not in the database : we let the user know
               ActionMessages errors = new ActionMessages();
               // errors.add("email", new ActionMessage("invalid.email", email));
               this.saveErrors(request, errors);
               return (mapping.findForward("failure1"));
                
            }
            
        } catch (SQLException ex) {
            String errorMessage = ex.getMessage();
            session.setAttribute("errorMessage", errorMessage);
            return (mapping.findForward("database_problem"));
        }
    }
}