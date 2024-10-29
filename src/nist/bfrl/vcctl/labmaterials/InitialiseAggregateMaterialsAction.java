/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import java.sql.SQLException;
import javax.servlet.http.*;
import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.exceptions.NoCoarseAggregateException;
import nist.bfrl.vcctl.exceptions.NoFineAggregateException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import org.apache.struts.action.*;

/**
 *
 * @author bullard
 */
public class InitialiseAggregateMaterialsAction extends Action {
    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) {

        AggregateMaterialsForm aggregateMaterialsForm = (AggregateMaterialsForm) form;
        String coarseAggName;
        String fineAggName;
        String coarseAggDisplayName;
        String fineAggDisplayName;
        try {

            Aggregate coarseAggregate;
            try {
                coarseAggregate = Aggregate.load(CementDatabase.getFirstCoarseAggregateDisplayName());
                aggregateMaterialsForm.setCoarseAggregate(coarseAggregate);
                coarseAggName = coarseAggregate.getName();
                coarseAggDisplayName = coarseAggregate.getDisplay_name();
                request.setAttribute("coarseAggName", coarseAggName);
            } catch (NoCoarseAggregateException ex) {
                return (mapping.findForward("no_coarse_aggregate"));
            }

            Aggregate fineAggregate;
            try {
                fineAggregate = Aggregate.load(CementDatabase.getFirstFineAggregateDisplayName());
                aggregateMaterialsForm.setFineAggregate(fineAggregate);
                fineAggName = fineAggregate.getName();
                fineAggDisplayName = fineAggregate.getDisplay_name();
                request.setAttribute("fineAggName", fineAggName);
            } catch (NoFineAggregateException ex) {
                return (mapping.findForward("no_fine_aggregate"));
            }

        } catch (SQLException ex) {
            return mapping.findForward("database_problem");
        } catch (SQLArgumentException ex) {
            ex.printStackTrace();
        }

        return (mapping.findForward("success"));
    }
}
