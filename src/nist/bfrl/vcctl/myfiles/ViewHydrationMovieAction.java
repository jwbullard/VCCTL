/*
 * ViewImageAction.java
 *
 * Created on February 13, 2006, 11:28 AM
 */

package nist.bfrl.vcctl.myfiles;


import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import nist.bfrl.vcctl.database.User;
import nist.bfrl.vcctl.myoperations.*;
import nist.bfrl.vcctl.database.Operation;
import nist.bfrl.vcctl.database.OperationDatabase;
import nist.bfrl.vcctl.util.Constants;

import org.apache.struts.action.*;
import org.apache.struts.action.Action;
import org.apache.struts.action.ActionForm;
import org.apache.struts.action.ActionMapping;
import org.apache.struts.action.ActionForward;

import java.io.*;
import nist.bfrl.vcctl.image.HydrationMovie;

/**
 *
 * @author tahall
 * @version
 */

public class ViewHydrationMovieAction extends Action {
    
    /* forward name="success" path="" */
    private final static String VIEW_MOVIE = "view-hydration-movie";
    private final static String VIEW_OPERATION_FILES = "view-operation-files";
    private final static String OPS_HOME = "my-operations-home";
    
    /**
     * This is the action called from the Struts framework.
     * @param mapping The ActionMapping used to select this instance.
     * @param form The optional ActionForm bean for this request.
     * @param request The HTTP Request we are processing.
     * @param response The HTTP Response we are processing.
     * @throws java.lang.Exception
     * @return
     */
    public ActionForward execute(ActionMapping mapping,
            ActionForm  form,
            HttpServletRequest request,
            HttpServletResponse response)
            throws Exception {

        ViewHydrationMovieForm viewHydrationMovieForm = (ViewHydrationMovieForm)form;
        
        User user = (User)request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {

                String operationName = request.getParameter("operation");
                String operationType = "";
                if (operationName != null) {
                    Operation op = OperationDatabase.getOperationForUser(operationName,userName);
                    operationType = op.getType();
                    viewHydrationMovieForm.setOptype(operationType);
                    viewHydrationMovieForm.setOpname(operationName);
                }

                String fileName = request.getParameter("file");
                if (fileName != null) {
                    viewHydrationMovieForm.setName(fileName);
                }

                operationName = viewHydrationMovieForm.getOpname();
                fileName = viewHydrationMovieForm.getName();
                
                if (operationName != null && fileName != null) {                    
                    int magnification = Integer.parseInt(viewHydrationMovieForm.getMagnification());
                    int bse = 0;
                    if (viewHydrationMovieForm.getBse().equalsIgnoreCase("yes")) {
                        bse = 1;
                    }
                    String foundframespeed = viewHydrationMovieForm.getFramespeed();
                    double framespeed = Double.parseDouble(foundframespeed);
                    
                    /**
                     * Generate the hydration movie
                     */
                    HydrationMovie hm = HydrationMovie.INSTANCE;
                    
                    String moviename = hm.createMovie(userName, operationName, fileName, bse, magnification, framespeed);
                    
                    viewHydrationMovieForm.setMovieName(moviename);
                    
                    return mapping.findForward("success");
                } else {
                    return mapping.findForward("movie_not_found");
                }
            } else {
                return mapping.findForward("no_user");
            }
        } else {
            return mapping.findForward("no_user");
        }
    }
}
