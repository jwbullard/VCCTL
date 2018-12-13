/*
 * MeasureConcreteMicrostructureAction.java
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
public class MeasureConcreteMicrostructureAction extends Action {

    @Override
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest request,
            HttpServletResponse response) throws Exception {

        Map pm = request.getParameterMap();
        HttpSession session = request.getSession();
        ConcreteMeasurementsForm measurementsForm = (ConcreteMeasurementsForm) form;


        User user = (User) request.getSession().getAttribute("user");
        if (user != null) {
            String userName = user.getName();
            if (!userName.equalsIgnoreCase("")) {
                if (pm.containsKey("action")) {
                    String[] actions = (String[]) pm.get("action");
                    String action = actions[0];

                    if (action.equalsIgnoreCase("change_mix")) {
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

                        return mapping.findForward("mix_changed");
                    } else if (action.equalsIgnoreCase("measure_elastic_moduli")) {
                        String time = request.getParameter("time");
                        HydratedImage hydratedImage = measurementsForm.getHydratedImagesList(time);

                        String operationName = measurementsForm.getHydrationName();

                        String outputDirectory = Constants.ELASTIC_OPERATION_NAME_ROOT + hydratedImage.getNumber();

                        operationName = operationName + File.separator + outputDirectory;

                        outputDirectory = ServerFile.getUserOperationDir(userName, operationName);

                        String elasticInput = measurementsForm.generateElasticInputForUser(hydratedImage.getName(), outputDirectory, operationName, userName);
                        // operationName = operationName.replace(".img", ".ela");

                        ServerFile.writeUserOpTextFile(userName, operationName, "elastic.in", elasticInput);

                        Operation operation = new Operation(operationName, userName, Constants.ELASTIC_MODULI_OPERATION_TYPE);

                        byte[] state = OperationState.save_to_Xml(measurementsForm);
                        operation.setState(state);
                        OperationDatabase.queueOperation(operation);

                        return mapping.findForward("measuring_elastic_moduli");
                    } else if (action.equalsIgnoreCase("measure_transport_factor")) {
                        String time = request.getParameter("time");
                        HydratedImage hydratedImage = measurementsForm.getHydratedImagesList(time);

                        String operationName = measurementsForm.getHydrationName();
                        String outputDirectory = Constants.TRANSPORT_OPERATION_NAME_ROOT + hydratedImage.getNumber();

                        operationName = operationName + File.separator + outputDirectory;

                        outputDirectory = ServerFile.getUserOperationDir(userName, operationName);

                        String transportInput = measurementsForm.generateTransportInputForUser(hydratedImage.getName(), outputDirectory, operationName, userName);
                        // operationName = operationName.replace(".img", ".ela");

                        ServerFile.writeUserOpTextFile(userName, operationName, "transport.in", transportInput);

                        Operation operation = new Operation(operationName, userName, Constants.TRANSPORT_FACTOR_OPERATION_TYPE);

                        byte[] state = OperationState.save_to_Xml(measurementsForm);
                        operation.setState(state);
                        OperationDatabase.queueOperation(operation);

                        return mapping.findForward("measuring_transport_factor");
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
}
