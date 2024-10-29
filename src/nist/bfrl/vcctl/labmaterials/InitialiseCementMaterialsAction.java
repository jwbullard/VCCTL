/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import java.sql.SQLException;
import javax.servlet.http.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.exceptions.DBFileException;
import nist.bfrl.vcctl.exceptions.NoCementException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;

/**
 *
 * @author bullard
 */
public class InitialiseCementMaterialsAction extends Action {
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {

        CementMaterialsForm cementMaterialsForm = (CementMaterialsForm) form;
        Cement cement;
        try {
            try {
                cement = Cement.load(Constants.DEFAULT_CEMENT);
                cementMaterialsForm.setCement(cement);
                // cementMaterialsForm.setCemName(cement);
            } catch (SQLArgumentException ex) {
                try {
                    cement = Cement.load(CementDatabase.getFirstCementName());
                    cementMaterialsForm.setCement(cement);
                   // cementMaterialsForm.setCemName(cement);
                } catch (NoCementException exc) {
                    return (mapping.findForward("no_cement"));
                }
                ex.printStackTrace();
            }
            String cemName = cement.getName();
            request.setAttribute("cemName", cemName);

            DBFile cementDataFile;
            try {
                cementDataFile = DBFile.load(CementDatabase.getFirstCementDataFileName());
                cementMaterialsForm.setCementDataFile(cementDataFile);
            } catch (DBFileException ex) {
                return (mapping.findForward("no_cement_data_file"));
            }

        } catch (SQLException ex) {
            return mapping.findForward("database_problem");
        } catch (SQLArgumentException ex) {
            ex.printStackTrace();
        }

        return (mapping.findForward("success"));
    }
}
