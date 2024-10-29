/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.admin;

import java.sql.SQLException;
import javax.servlet.http.*;
import nist.bfrl.vcctl.database.User;
import nist.bfrl.vcctl.database.UserDatabase;
import nist.bfrl.vcctl.database.VCCTLDatabase;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import org.apache.struts.action.*;

import java.io.File;
import java.io.IOException;
import nist.bfrl.vcctl.application.Vcctl;

/**
 *
 * @author bullard
 */
public final class InitializeLogoutAction extends Action {

    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {


        Vcctl.setUserName("");
        
        return (mapping.findForward("success"));
    }
}