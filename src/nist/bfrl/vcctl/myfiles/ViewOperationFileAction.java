/*
 * ViewOperationFileAction.java
 *
 * Created on November 25, 2005, 2:18 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.myfiles;

import javax.servlet.http.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.database.User;
import org.apache.struts.action.*;

import nist.bfrl.vcctl.util.*;

/**
 *
 * @author tahall
 */
public class ViewOperationFileAction extends Action {
    
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {
        
        String fileName = request.getParameter("file");
        String opname = request.getSession().getAttribute("opname").toString();
        
        User user = (User)request.getSession().getAttribute("user");
        String userName = user.getName();
        
        /**
         *  Determine if the file to be viewed is a 3-D microstructure image.
         *  They are treated differently.
         */
        boolean isImage = false;
        if (fileName.equalsIgnoreCase(opname) && fileName.endsWith(".img")) {
            isImage = true;
        }
        if (opname.endsWith(".run")) {
            /**
             * This is a hydration run
             */
            if (fileName.contains(".img.")) {
                isImage = true;
            }
        }
        
        byte[] fileBytes;
        if (isImage) {
            request.getSession().setAttribute("imagename", fileName);
            request.getSession().setAttribute("opname", opname);
            return (mapping.findForward("viewimage"));
        } else if (fileName.equalsIgnoreCase("p"+opname)) {
            String pifText = "Cannot view particle image files";
            fileBytes = pifText.getBytes();
        } else {
            fileBytes  = ServerFile.readUserOpBinaryFile(userName, opname, fileName);
        }
        
        String optext = new String(fileBytes);
        request.getSession().setAttribute("filename", fileName);
        request.getSession().setAttribute("optext", optext);
        
        return (mapping.findForward("viewtext"));
    }
    
}
