# usage: brep2step.py in.brep out.step [solid_index]  -- writes one solid (largest by volume when the file holds several) as AP214 STEP
import sys
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.Interface import Interface_Static
s=TopoDS_Shape(); BRepTools.Read_s(s,sys.argv[1],BRep_Builder())
sol=[]; e=TopExp_Explorer(s,TopAbs_SOLID)
while e.More():
    g=GProp_GProps(); BRepGProp.VolumeProperties_s(e.Current(),g); sol.append((abs(g.Mass()),TopoDS.Solid(e.Current()))); e.Next()
sol.sort(key=lambda x:-x[0])
Interface_Static.SetCVal_s("write.step.schema","AP214IS")
w=STEPControl_Writer(); w.Transfer(sol[0][1],STEPControl_AsIs); w.Write(sys.argv[2])
print(sys.argv[2], len(sol), 'solids, kept volume', sol[0][0])
