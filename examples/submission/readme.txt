To start testing the test_[cp,ph,pw].py:

1. setup AiiDA 
2. setup and configure at least one computer in AiiDA, using
     verdi computer setup COMPUTERNAME
   followed by
     verdi computer configure COMPUTERNAME
3. setup at least a code on that machine (cp.x if you want to try test_cp.py,
   and so on) using
     verdi code setup
4. Upload at least a pseudopotential family (or edit test_pw.py and set
   auto_pseudos to False to use the provided three potentials for BaTiO3)
   using the upload_pseudo_family.py code in this folder.
5. Run the test_*.py file passing as a parameter the code label you chose in
   the code setup process.

Other tests work in a similar way.
