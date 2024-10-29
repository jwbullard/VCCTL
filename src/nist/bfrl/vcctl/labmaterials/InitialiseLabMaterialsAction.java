/*
 * EditLabMaterialsAction.java
 *
 * Created on May 6, 2005, 11:56 AM
 */
package nist.bfrl.vcctl.labmaterials;

import java.sql.SQLException;
import javax.servlet.http.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.exceptions.DBFileException;
import nist.bfrl.vcctl.exceptions.NoCementException;
import nist.bfrl.vcctl.exceptions.NoFlyAshException;
import nist.bfrl.vcctl.exceptions.NoInertFillerException;
import nist.bfrl.vcctl.exceptions.NoSlagException;
import nist.bfrl.vcctl.exceptions.NoCoarseAggregateException;
import nist.bfrl.vcctl.exceptions.NoFineAggregateException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import org.apache.struts.action.*;

/**
 *
 * @author tahall
 */
public final class InitialiseLabMaterialsAction extends Action {

    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {

        LabMaterialsForm labMaterialsForm = (LabMaterialsForm) form;
        Cement cement;
        try {
            try {
                cement = Cement.load(Constants.DEFAULT_CEMENT);
                labMaterialsForm.setCement(cement);
                labMaterialsForm.setCemName(cement);
            } catch (SQLArgumentException ex) {
                try {
                    cement = Cement.load(CementDatabase.getFirstCementName());
                    labMaterialsForm.setCement(cement);
                    labMaterialsForm.setCemName(cement);
                } catch (NoCementException exc) {
                    return (mapping.findForward("no_cement"));
                }
                ex.printStackTrace();
            }

            Slag slag;
            try {
                slag = Slag.load(CementDatabase.getFirstSlagName());
                labMaterialsForm.setSlag(slag);
            } catch (NoSlagException ex) {
                return (mapping.findForward("no_slag"));
            }

            FlyAsh flyAsh;
            try {
                flyAsh = FlyAsh.load(CementDatabase.getFirstFlyAshName());
                labMaterialsForm.setFlyAsh(flyAsh);
            } catch (NoFlyAshException ex) {
                return (mapping.findForward("no_fly_ash"));
            }

            InertFiller inertFiller;
            try {
                inertFiller = InertFiller.load(CementDatabase.getFirstInertFillerName());
                labMaterialsForm.setInertFiller(inertFiller);
            } catch (NoInertFillerException ex) {
                return (mapping.findForward("no_inert_filler"));
            }

            Aggregate coarseAggregate;
            try {
                coarseAggregate = Aggregate.load(CementDatabase.getFirstCoarseAggregateName());
                labMaterialsForm.setCoarseAggregate(coarseAggregate);
            } catch (NoCoarseAggregateException ex) {
                return (mapping.findForward("no_coarse_aggregate"));
            }

            Aggregate fineAggregate;
            try {
                fineAggregate = Aggregate.load(CementDatabase.getFirstFineAggregateName());
                labMaterialsForm.setFineAggregate(fineAggregate);
            } catch (NoFineAggregateException ex) {
                return (mapping.findForward("no_fine_aggregate"));
            }

            DBFile cementDataFile;
            try {
                cementDataFile = DBFile.load(CementDatabase.getFirstCementDataFileName());
                labMaterialsForm.setCementDataFile(cementDataFile);
            } catch (DBFileException ex) {
                return (mapping.findForward("no_cement_data_file"));
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
