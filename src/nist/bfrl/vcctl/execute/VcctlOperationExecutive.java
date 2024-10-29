/*
 * VcctlOperationExecutive.java
 *
 * Created on September 9, 2005, 11:12 AM
 *
 * To change this template, choose Tools | Options and locate the template under
 * the Source Creation and Management node. Right-click the template and choose
 * Open. You can then make changes to the template in the Source Editor.
 */
package nist.bfrl.vcctl.execute;

import java.util.concurrent.*;
import java.util.*;

import nist.bfrl.vcctl.database.*;
import nist.bfrl.vcctl.operation.*;
import nist.bfrl.vcctl.operation.microstructure.genaggpack.GenAggPack;
import nist.bfrl.vcctl.operation.microstructure.genmic.*;
import nist.bfrl.vcctl.operation.hydration.*;
import nist.bfrl.vcctl.measurements.Elastic;
import nist.bfrl.vcctl.measurements.TransportFactor;
import nist.bfrl.vcctl.util.Constants;

/**
 *
 * @author tahall
 */
public class VcctlOperationExecutive {

    /** Creates a new instance of VcctlOperationExecutive */
    public VcctlOperationExecutive() {
    }

    static public Cancellable start(Operation op) {
        String type = op.getType();
        String name = op.getName();
        Future<String> future = null;
        if (type.equalsIgnoreCase(Constants.MICROSTUCTURE_OPERATION_TYPE)) {
            ExecutorService executor = Executors.newSingleThreadExecutor();
            GenMic gm = new GenMic(op);
            future = executor.submit(gm);
            return gm;
        } else if (type.equalsIgnoreCase(Constants.HYDRATION_OPERATION_TYPE)) {
            ExecutorService executor = Executors.newSingleThreadExecutor();
            HydMic hm = new HydMic(op);
            future = executor.submit(hm);
            return hm;
        } else if (type.equalsIgnoreCase(Constants.ELASTIC_MODULI_OPERATION_TYPE)) {
            ExecutorService executor = Executors.newSingleThreadExecutor();
            Elastic cpe = new Elastic(op);
            future = executor.submit(cpe);
            return cpe;
        } else if (type.equalsIgnoreCase(Constants.TRANSPORT_FACTOR_OPERATION_TYPE)) {
            ExecutorService executor = Executors.newSingleThreadExecutor();
            TransportFactor tfe = new TransportFactor(op);
            future = executor.submit(tfe);
            return tfe;
        } else if (type.equalsIgnoreCase(Constants.AGGREGATE_OPERATION_TYPE)) {
            ExecutorService executor = Executors.newSingleThreadExecutor();
            GenAggPack genAggPack = new GenAggPack(op);
            future = executor.submit(genAggPack);
            return genAggPack;
        }

        return null;
    }
}
