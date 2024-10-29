/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package nist.bfrl.vcctl.labmaterials;

import nist.bfrl.vcctl.database.Aggregate;

/**
 *
 * @author bullard
 */
public class AggregateUploadResult {
    private Aggregate aggregate;
    private String shapeZIPFile;
    private boolean shapeZIPFilePresent;

    public AggregateUploadResult(Aggregate aggregate,boolean shapeZIPFilePresent) {
        this.aggregate = aggregate;
    }

    public Aggregate getAggregate() {
        return aggregate;
    }

    public void setAggregate(Aggregate aggregate) {
        this.aggregate = aggregate;
    }

    public String getShapeZIPFile() {
        return shapeZIPFile;
    }

    public void setShapeZIPFile(String zf) {
        this.shapeZIPFile = zf;
    }

    public boolean getShapeZIPFilePresent() {
        return shapeZIPFilePresent;
    }

    public void setShapeZIPFilePresent(boolean val) {
        this.shapeZIPFilePresent = val;
    }

}
