with import <nixpkgs> {};

let
  py = pks.python38;
  fsh = pkgs.writeShellScriptBin "fsh" '' '';
in stdenv.mkDerivation {
    name = "135Server";
    buildInputs = [
      py
      py.pkgs.flask
      py.pkgs.isdangerous
      pkgs.figlet
      pkgs.lolcat
      fsh
    ];
    installPhase = ''
      export FLASK_APP=shisanwu.py
    '';
    shellHook = ''
      figlet "Welcome to 135 server project."
      echo "using python ${py.name}"
      echo $FLASK_APP
    '';

  }
