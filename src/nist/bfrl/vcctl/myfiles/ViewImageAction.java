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
import nist.bfrl.vcctl.image.ImageSlice;

/**
 *
 * @author tahall
 * @version
 */

public class ViewImageAction extends Action {
    
    /* forward name="success" path="" */
    private final static String VIEW_SLICE = "view-slice";
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

        ViewImageForm viewImageForm = (ViewImageForm)form;
        
        User user = (User)request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {

                String operationName = request.getParameter("operation");
                String operationType = "";
                if (operationName != null) {
                    Operation op = OperationDatabase.getOperationForUser(operationName,userName);
                    operationType = op.getType();
                    viewImageForm.setOptype(operationType);
                    viewImageForm.setOpname(operationName);
                }

                String fileName = request.getParameter("file");
                if (fileName != null) {
                    viewImageForm.setName(fileName);
                }

                operationName = viewImageForm.getOpname();
                fileName = viewImageForm.getName();
                
                if (operationName != null && fileName != null) {                    
                    /**
                     * Convert 'plane' from string to number
                     * 1:  xy plane
                     * 2:  xz plane
                     * 3:  yz plane
                     */
                    int plane = 3; // yz-plane is default
                    if (viewImageForm.getPlane().equalsIgnoreCase("xz")) {
                        plane = 2;
                    } else if (viewImageForm.getPlane().equalsIgnoreCase("xy")) {
                        plane = 1;
                    }
                    
                    int sliceNumber = Integer.parseInt(viewImageForm.getSliceNumber());
                    int magnification = Integer.parseInt(viewImageForm.getMagnification());

                    int viewdepth = 0;
                    if (viewImageForm.getViewdepth().equalsIgnoreCase("yes")) {
                        viewdepth = 1;
                    }

                    int bse = 0;
                    if (viewImageForm.getBse().equalsIgnoreCase("yes")) {
                        bse = 1;
                    }

                    /**
                     * Generate the 2-D image slice
                     */
                    ImageSlice is = ImageSlice.INSTANCE;
                    
                    String slicename = is.createSlice(userName, operationName, fileName, plane, sliceNumber, viewdepth, bse, magnification);
                    
                    viewImageForm.setSliceName(slicename);
                    
                    return mapping.findForward("success");
                } else {
                    return mapping.findForward("image_not_found");
                }
            } else {
                return mapping.findForward("no_user");
            }
        } else {
            return mapping.findForward("no_user");
        }
    }
}
