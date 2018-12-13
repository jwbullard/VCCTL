/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import java.sql.SQLException;
import javax.servlet.http.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.exceptions.DBFileException;
import nist.bfrl.vcctl.exceptions.NoFlyAshException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;
/**
 *
 * @author bullard
 */
public class InitialiseFlyAshMaterialsAction extends Action {
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {

        FlyAshMaterialsForm flyAshMaterialsForm = (FlyAshMaterialsForm) form;
        try {

            FlyAsh flyAsh;
            try {
                flyAsh = FlyAsh.load(CementDatabase.getFirstFlyAshName());
                flyAshMaterialsForm.setFlyAsh(flyAsh);
            } catch (NoFlyAshException ex) {
                return (mapping.findForward("no_fly_ash"));
            }

        } catch (SQLException ex) {
            return mapping.findForward("database_problem");
        } catch (DBFileException ex) {
            if (ex.getErrorType().equalsIgnoreCase(Constants.NO_DATA_OF_THIS_TYPE) && ex.getType().equalsIgnoreCase(Constants.PSD_TYPE)) {
                return (mapping.findForward("no_psd"));
            }
        } catch (SQLArgumentException ex) {
            ex.printStackTrace();
        }

        return (mapping.findForward("success"));
    }
}
