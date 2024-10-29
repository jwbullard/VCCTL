/*
 * EditMmicrostructureFilesAction.java
 *
 * Created on October 28, 2011, 3:00 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.myfiles;

import java.util.Map;
import javax.servlet.http.*;
import nist.bfrl.vcctl.database.User;
import org.apache.struts.action.*;

/**
 *
 * @author mscialom
 */
public class EditMicrostructureFilesAction extends Action {

    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {

        MyMicrostructureFilesForm myFilesForm = (MyMicrostructureFilesForm)form;

        HttpSession session = request.getSession();

        Map pm = request.getParameterMap();

        User user = (User)request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {

                return (mapping.findForward("success"));
            } else {
                return mapping.findForward("no_user");
            }
        } else {
            return mapping.findForward("no_user");
        }
    }

}
