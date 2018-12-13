/*
 * InitializeConcreteMeasurementsAction.java
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
public class InitializeConcreteMeasurementsAction extends Action {

    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws IOException {


        User user = (User) request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {

                try {
                    ConcreteMeasurementsForm measurementsForm = (ConcreteMeasurementsForm) form;
                    
                    List<String> hydratedMixList;
                    hydratedMixList = OperationDatabase.finishedRunningOrQueuedOperationsNamesOfTypeForUser(Constants.HYDRATION_OPERATION_TYPE, userName);

                    if (hydratedMixList != null && hydratedMixList.size() > 0) {
                        measurementsForm.setUserFinishedHydratedMixList(hydratedMixList);
                        String hydrationName = hydratedMixList.get(0);
                        measurementsForm.setHydrationName(hydrationName);
                        measurementsForm.setMicrostructure(OperationDatabase.getDependantOperationForUser(hydrationName, userName));
                    } else {
                        return mapping.findForward("no_hydrated_mix_for_user");
                    }
                    
                    try {
                        measurementsForm.init(userName);
                    } catch (NoHydrationResultsException ex) {
                        ActionMessages errors = new ActionMessages();
                        errors.add("no-results", new ActionMessage("no-results", measurementsForm.getHydrationName()));
                        this.saveErrors(request, errors);

                        return (mapping.findForward("no_results"));
                    }

                    /**
                     * Get image files
                     **/
                    String imageIndexFileContent = ServerFile.readUserOpTextFile(userName, measurementsForm.getHydrationName(), Constants.IMAGES_LIST_FILENAME);
                    String[] lines = imageIndexFileContent.split("\n");
                    String measurementTime, imageName;
                    HydratedImage hydratedImage;
                    TreeMap<String, HydratedImage> hydratedImagesList = new TreeMap();
                    if (lines != null) {
                        for (int i = 0; i < lines.length; i++) {
                            if (!lines[i].equalsIgnoreCase("")) {
                                String lineElements[] = lines[i].split("\t");
                                if (lineElements != null) {
                                    measurementTime = lineElements[0];
                                    double time = Math.round(Double.parseDouble(measurementTime) * 10.0) / 10.0; // round to 1 dec
                                    measurementTime = Double.toString(time);
                                    imageName = lineElements[1];
                                    hydratedImage = new HydratedImage(imageName, measurementTime, i, userName, measurementsForm.getHydrationName());
                                    hydratedImagesList.put(measurementTime, hydratedImage);
                                }
                            }
                        }
                        measurementsForm.setHydratedImagesList(hydratedImagesList);
                    }
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
