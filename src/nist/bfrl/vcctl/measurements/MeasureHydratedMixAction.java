/*
 * MeasureHydratedMixAction.java
 *
 * Created on July 21, 2007, 6:47 PM
 *
 * To change this template, choose Tools | Template Manager
 * and open the template in the editor.
 */
package nist.bfrl.vcctl.measurements;

import java.io.File;
import java.util.Map;
import java.util.TreeMap;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import nist.bfrl.vcctl.database.Operation;
import nist.bfrl.vcctl.database.OperationDatabase;
import nist.bfrl.vcctl.database.User;
import nist.bfrl.vcctl.exceptions.NoHydrationResultsException;
import nist.bfrl.vcctl.operation.OperationState;
import nist.bfrl.vcctl.util.Constants;
import nist.bfrl.vcctl.util.ServerFile;
import org.apache.struts.action.*;
import org.jfree.chart.*;
import org.jfree.chart.entity.*;

/**
 *
 * @author mscialom
 */
public class MeasureHydratedMixAction extends Action {

    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws Exception {

        Map pm = request.getParameterMap();
        HttpSession session = request.getSession();
        HydratedMixMeasurementsForm measurementsForm = (HydratedMixMeasurementsForm) form;


        User user = (User) request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {
                if (pm.containsKey("action")) {
                    String[] actions = (String[]) pm.get("action");
                    String action = actions[0];

                    if (action.equalsIgnoreCase("change_plotting_element")) {

                        JFreeChart jFreeChart = measurementsForm.generateGraph();

                        ServletChart chart = ServletChartMaker.createSmallPNGChart(jFreeChart, request);

                        measurementsForm.setChartXMax(chart.getXMaxValue());
                        measurementsForm.setChartXMin(chart.getXMinValue());

                        request.setAttribute("chart", chart);

                        return mapping.findForward("measuring_hydrated_mix");
                    } else if (action.equalsIgnoreCase("change_mix")) {

                        JFreeChart jFreeChart = measurementsForm.generateGraphFromNewMix(userName);

                        ServletChart chart = ServletChartMaker.createSmallPNGChart(jFreeChart, request);

                        measurementsForm.setChartXMax(chart.getXMaxValue());
                        measurementsForm.setChartXMin(chart.getXMinValue());

                        request.setAttribute("chart", chart);

                        return mapping.findForward("measuring_hydrated_mix");
                    } else if (action.equalsIgnoreCase("add_y_plotting_element")) {

                        measurementsForm.addYPlottingElement();

                        JFreeChart jFreeChart = measurementsForm.generateGraph();

                        ServletChart chart = ServletChartMaker.createSmallPNGChart(jFreeChart, request);

                        measurementsForm.setChartXMax(chart.getXMaxValue());
                        measurementsForm.setChartXMin(chart.getXMinValue());

                        request.setAttribute("chart", chart);

                        return mapping.findForward("y_plotting_element_added");
                    } else if (action.equalsIgnoreCase("remove_y_plotting_element")) {

                        if (pm.containsKey("yPlottingElementToRemove")) {
                            String[] yPlottingElementToRemoves = (String[]) pm.get("yPlottingElementToRemove");
                            String yPlottingElementToRemove = yPlottingElementToRemoves[0];
                            measurementsForm.removeYPlottingElement(Integer.parseInt(yPlottingElementToRemove));
                        }
                        JFreeChart jFreeChart = measurementsForm.generateGraph();

                        ServletChart chart = ServletChartMaker.createSmallPNGChart(jFreeChart, request);

                        measurementsForm.setChartXMax(chart.getXMaxValue());
                        measurementsForm.setChartXMin(chart.getXMinValue());

                        request.setAttribute("chart", chart);

                        return mapping.findForward("y_plotting_element_removed");
                    } else if (action.equalsIgnoreCase("display_big_chart")) {
                        JFreeChart jFreeChart = measurementsForm.generateGraph();

                        ServletChart chart = ServletChartMaker.createBigPNGChart(jFreeChart, request);

                        measurementsForm.setChartXMax(chart.getXMaxValue());
                        measurementsForm.setChartXMin(chart.getXMinValue());

                        request.setAttribute("bigChart", chart);

                        return mapping.findForward("big_chart_generated");
                    } else if (action.equalsIgnoreCase("change_graph_boundaries")) {
                        if (pm.containsKey("lowerBound") && pm.containsKey("upperBound")) {
                            String[] lowerBounds = (String[]) pm.get("lowerBound");
                            double lowerBound = Double.parseDouble(lowerBounds[0]);
                            String[] upperBounds = (String[]) pm.get("upperBound");
                            double upperBound = Double.parseDouble(upperBounds[0]);
                            JFreeChart jFreeChart = measurementsForm.generateGraph(lowerBound, upperBound);

                            ServletChart chart = ServletChartMaker.createSmallPNGChart(jFreeChart, request);
                            request.setAttribute("chart", chart);

                            measurementsForm.setChartXMax(chart.getXMaxValue());
                            measurementsForm.setChartXMin(chart.getXMinValue());

                            return mapping.findForward("boundaries_changed");
                        }
                    } else if (action.equalsIgnoreCase("change_big_graph_boundaries")) {
                        if (pm.containsKey("lowerBound") && pm.containsKey("upperBound")) {
                            String[] lowerBounds = (String[]) pm.get("lowerBound");
                            double lowerBound = Double.parseDouble(lowerBounds[0]);
                            String[] upperBounds = (String[]) pm.get("upperBound");
                            double upperBound = Double.parseDouble(upperBounds[0]);
                            JFreeChart jFreeChart = measurementsForm.generateGraph(lowerBound, upperBound);

                            ServletChart chart = ServletChartMaker.createBigPNGChart(jFreeChart, request);
                            request.setAttribute("bigChart", chart);

                            measurementsForm.setChartXMax(chart.getXMaxValue());
                            measurementsForm.setChartXMin(chart.getXMinValue());

                            return mapping.findForward("big_chart_generated");
                        }

                        return mapping.findForward("failure");
                    } else {
                        return mapping.findForward("measuring_hydrated_mix");
                    }
                } else {
                    return mapping.findForward("no_user");
                }
            } else {
                return mapping.findForward("no_user");
            }
        }
        return mapping.findForward("no_user");
    }
}
