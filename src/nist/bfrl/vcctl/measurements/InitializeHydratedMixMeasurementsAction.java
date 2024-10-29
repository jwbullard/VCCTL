/*
 * InitializeHydratedMixMeasurementsAction.java
 *
 * Created on July 21, 2007, 5:40 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */
package nist.bfrl.vcctl.measurements;

import java.io.IOException;
import java.sql.SQLException;
import java.util.List;
import java.util.TreeMap;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import nist.bfrl.vcctl.database.User;
import nist.bfrl.vcctl.database.OperationDatabase;
import nist.bfrl.vcctl.exceptions.NoHydrationResultsException;
import nist.bfrl.vcctl.exceptions.SQLArgumentException;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.ServerFile;
import org.apache.struts.action.*;
import org.jfree.chart.JFreeChart;

/**
 *
 * @author mscialom
 */
public class InitializeHydratedMixMeasurementsAction extends Action {

    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws IOException {


        User user = (User) request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            String hydrationName = "";
            HydrationResults hydrationResults;
            if (!userName.equalsIgnoreCase("")) {

                try {
                    HydratedMixMeasurementsForm measurementsForm = (HydratedMixMeasurementsForm) form;
                    
                    List<String> hydratedMixList;
                    hydratedMixList = OperationDatabase.finishedRunningOrQueuedOperationsNamesOfTypeForUser(Constants.HYDRATION_OPERATION_TYPE, userName);

                    if (hydratedMixList != null && hydratedMixList.size() > 0) {
                        measurementsForm.setUserFinishedHydratedMixList(hydratedMixList);
                        hydrationName = hydratedMixList.get(0);
                        hydrationResults = new HydrationResults(userName,hydrationName);
                        if (hydrationResults.getHydrationResultsArray() == null) {
                            return mapping.findForward("no_hydrated_results_ready_yet");
                        }
                    } else {
                        return mapping.findForward("no_hydrated_mix_for_user");
                    }
                    
                    try {
                        measurementsForm.init(userName,hydrationName,hydrationResults);
                    } catch (NoHydrationResultsException ex) {
                        ActionMessages errors = new ActionMessages();
                        errors.add("no-results", new ActionMessage("no-results", hydrationName));
                        this.saveErrors(request, errors);

                        return (mapping.findForward("no_results"));
                    }

                    JFreeChart jFreeChart = measurementsForm.generateGraph();

                    ServletChart chart = ServletChartMaker.createSmallPNGChart(jFreeChart, request);

                    measurementsForm.setChartXMax(chart.getXMaxValue());
                    measurementsForm.setChartXMin(chart.getXMinValue());

                    request.setAttribute("chart", chart);

                } catch (SQLException ex) {
                    return mapping.findForward("database_problem");
                } catch (SQLArgumentException ex) {
                    ex.printStackTrace();
                }

                return mapping.findForward("success");
            } else {
                return mapping.findForward("no_user");
            }
        } else {
            return mapping.findForward("no_user");
        }

    }
}
