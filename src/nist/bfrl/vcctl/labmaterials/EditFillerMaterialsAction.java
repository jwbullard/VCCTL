/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import java.io.IOException;
import java.io.PrintWriter;
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
public class EditFillerMaterialsAction extends Action {
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws IOException {

        FillerMaterialsForm fillerMaterialsForm = (FillerMaterialsForm) form;

        String action = request.getParameter("action");

        if (action != null) {
            try {
                if (action.equalsIgnoreCase("new_inert_filler")) {
                    InertFiller inertFiller = new InertFiller();
                    fillerMaterialsForm.setInertFiller(inertFiller);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("change_inert_filler")) {

                    String name = fillerMaterialsForm.getInertFiller().getName();

                    InertFiller inertFiller;
                    if (name == null || name.equalsIgnoreCase("")) {
                        inertFiller = new InertFiller();
                    } else {
                        inertFiller = InertFiller.load(name);
                        fillerMaterialsForm.setInertFiller(inertFiller);
                    }

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("update_inert_filler_characteristics")) {
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_inert_filler")) {
                    InertFiller inertFiller = fillerMaterialsForm.getInertFiller();
                    try {

                        inertFiller.save();
                    } catch (SQLException ex) {

                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_saving_inert_filler");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("save_inert_filler_as")) {
                    InertFiller inertFiller = fillerMaterialsForm.getInertFiller();

                    String name = request.getParameter("name");

                    PrintWriter out;
                    if (!CementDatabase.isUniqueInertFillerName(name)) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("inert_filler_name_alreadyTaken");
                        out.flush();
                        return null;
                    }

                    inertFiller.setName(name);
                    try {
                        inertFiller.saveAs();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("problem_when_saving_inert_filler");
                        out.flush();
                        return null;
                    }

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("delete_inert_filler")) {
                    InertFiller inertFiller = fillerMaterialsForm.getInertFiller();
                    try {
                        inertFiller.delete();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_deleteting_inert_filler");
                        out.flush();
                        return null;
                    }

                    try {
                        inertFiller = InertFiller.load(CementDatabase.getFirstInertFillerName());
                        fillerMaterialsForm.setInertFiller(inertFiller);
                    } catch (NoInertFillerException ex) {
                        return (mapping.findForward("no_inert_filler"));
                    }
                    return (mapping.findForward("success"));
                }
            } catch (DBFileException ex) {
                if (ex.getErrorType().equalsIgnoreCase(Constants.NO_DATA_OF_THIS_TYPE) && ex.getType().equalsIgnoreCase(Constants.PSD_TYPE)) {
                    return (mapping.findForward("no_psd"));
                }
            } catch (SQLArgumentException ex) {
                return (mapping.findForward("incorrect_name"));
            } catch (SQLException ex) {
                return mapping.findForward("database_problem");
            } catch (IOException ex) {
                ex.printStackTrace();
            }

            return (mapping.findForward("failure"));
        }
        return (mapping.findForward("success"));
    }
}
