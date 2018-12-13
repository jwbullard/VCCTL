/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import java.sql.SQLException;
import javax.servlet.http.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.exceptions.DBFileException;
import nist.bfrl.vcctl.exceptions.NoInertFillerException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;

/**
 *
 * @author bullard
 */
public class InitialiseFillerMaterialsAction extends Action {
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {

        FillerMaterialsForm fillerMaterialsForm = (FillerMaterialsForm) form;
        try {

            InertFiller inertFiller;
            try {
                inertFiller = InertFiller.load(CementDatabase.getFirstInertFillerName());
                fillerMaterialsForm.setInertFiller(inertFiller);
            } catch (NoInertFillerException ex) {
                return (mapping.findForward("no_inert_filler"));
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
