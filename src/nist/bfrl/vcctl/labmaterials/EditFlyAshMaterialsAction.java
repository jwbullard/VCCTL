/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.PrintWriter;
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
public class EditFlyAshMaterialsAction extends Action {
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws IOException {

        FlyAshMaterialsForm flyAshMaterialsForm = (FlyAshMaterialsForm) form;

        String action = request.getParameter("action");

        if (action != null) {
            try {
                if (action.equalsIgnoreCase("new_fly_ash")) {
                    FlyAsh flyAsh = new FlyAsh();
                    flyAshMaterialsForm.setFlyAsh(flyAsh);

                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("sum_fly_ash_vol_frac")) {
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("change_fly_ash")) {

                    String name = flyAshMaterialsForm.getFlyAsh().getName();

                    FlyAsh flyAsh;
                    if (name == null || name.equalsIgnoreCase("")) {
                        flyAsh = new FlyAsh();
                    } else {
                        flyAsh = FlyAsh.load(name);
                        flyAshMaterialsForm.setFlyAsh(flyAsh);
                        return (mapping.findForward("success"));
                    }

                } else if (action.equalsIgnoreCase("save_fly_ash")) {
                    FlyAsh flyAsh = flyAshMaterialsForm.getFlyAsh();

                    try {
                        flyAsh.save();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_saving_fly_ash");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));

                } else if (action.equalsIgnoreCase("save_fly_ash_as")) {
                    FlyAsh flyAsh = flyAshMaterialsForm.getFlyAsh();

                    String name = request.getParameter("name");

                    PrintWriter out;
                    if (!CementDatabase.isUniqueFlyAshName(name)) {
                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("fly_ash_name_alreadyTaken");
                        out.flush();
                        return null;
                    }

                    flyAsh.setName(name);
                    try {
                        flyAsh.saveAs();
                    } catch (SQLException ex) {

                        response.setContentType("text/html");
                        out = response.getWriter();
                        out.print("problem_when_saving_fly_ash");
                        out.flush();
                        return null;
                    }
                    return (mapping.findForward("success"));
                } else if (action.equalsIgnoreCase("delete_fly_ash")) {
                    FlyAsh flyAsh = flyAshMaterialsForm.getFlyAsh();
                    try {
                        flyAsh.delete();
                    } catch (SQLException ex) {
                        response.setContentType("text/html");
                        PrintWriter out = response.getWriter();
                        out.print("problem_when_deleteting_fly_ash");
                        out.flush();
                        return null;
                    }

                    try {
                        flyAsh = FlyAsh.load(CementDatabase.getFirstFlyAshName());
                        flyAshMaterialsForm.setFlyAsh(flyAsh);
                    } catch (NoFlyAshException ex) {
                        return (mapping.findForward("no_fly_ash"));
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
