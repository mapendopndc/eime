from libraries.eime import EngineeringProcedure

def GlulamBending(
        KD=None,
        Fb=None,
        KZbg=None,
        S=None,
        lambda1=None, lambda_e=None,
        KL_a=None, KL_b=None, KL=None,
        MrA=None, Mr1=None, Mr2=None, MrB=None, Mr=None
        ) -> EngineeringProcedure:
    
    procedure = EngineeringProcedure("Glulam Beam Bending Procedure")
    procedure.AddComputation(KD)
    procedure.AddComputation(Fb)
    procedure.AddComputation(lambda1)
    procedure.AddComputation(lambda_e)
    procedure.AddComputation(KL, show_util=False)
    procedure.AddComputation(KZbg, show_util=False)
    procedure.AddComputation(S)
    procedure.AddComputation(Mr)
    return procedure

def GlulamShear(KD=None,CV=None,Fv=None,Wr=None,Vr=None) -> EngineeringProcedure:
    procedure = EngineeringProcedure("Glulam Beam Shear Procedure")
    procedure.AddComputation(KD)
    procedure.AddComputation(CV)
    procedure.AddComputation(Fv)
    procedure.AddComputation(Wr)
    procedure.AddComputation(Vr)
    return procedure

def GlulamCompression(KD=None,Fc=None,KZcg=None,CC=None,KC=None, Pr=None) -> EngineeringProcedure:
    procedure = EngineeringProcedure("Glulam Beam Shear Procedure")
    procedure.AddComputation(KD)
    procedure.AddComputation(Fc)
    procedure.AddComputation(KZcg, show_util=False)
    procedure.AddComputation(CC)
    procedure.AddComputation(KC)
    procedure.AddComputation(Pr)
    return procedure