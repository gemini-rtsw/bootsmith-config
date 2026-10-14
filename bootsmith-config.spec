# RPM for the Bootsmith presets: every *.json in this repo, installed into the
# directory the bootsmith service mounts into its container.
#
# Updating presets on a boot server is installing a newer build of this
# package. Pin the full NVR (release ordering follows the git hash, not age):
#
#     dnf install bootsmith-config-<version>-<release>
#
# THE VERSION LIVES HERE. Bump specver for a change worth naming; every build
# is already unique by its git hash.
%global specver 1.0.0

# $GIT_HASH first: build_rpm.sh computes it on the host and passes it into the
# build container, where git alone can resolve to "nogit".
%define git_hash %(if [ -n "$GIT_HASH" ]; then echo "$GIT_HASH"; else git rev-parse --short HEAD 2>/dev/null || echo nogit; fi)
%global profdir %{_sharedstatedir}/bootsmith/profiles

Name:           bootsmith-config
Version:        %{specver}
Release:        1.git%{git_hash}%{?dist}
Summary:        Bootsmith presets: VME crate boot profiles

License:        Proprietary
URL:            https://github.com/gemini-rtsw/bootsmith-config
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
# bootsmith owns the directory (0777, so the app can write). Before 0.2.0 it
# also unpacked a git clone into it on first install, moving any files already
# there out of the way. Not a Requires: the pipeline's lightweight dev image has
# no rpm-repo to resolve it from, and nothing here needs bootsmith at install.
Conflicts:      bootsmith < 0.2.0
Recommends:     bootsmith >= 0.2.0

%description
The Bootsmith target profiles (presets), one JSON file per crate, installed in
%{profdir}.

Presets are %%config files. On an upgrade:
  - a preset you have not edited on this host is replaced by the new one;
  - a preset edited on this host (in the web UI) that the new package also
    changes is replaced, and your edit is kept as <name>.json.rpmsave;
  - a preset edited on this host that the new package does not change is
    left as you edited it.
Presets created in the UI are not package files and are never touched.
Commit any change you want to keep to the bootsmith-config repo.

%prep
%autosetup

%build
# Nothing to build. Refuse a preset that is not valid JSON or whose file name
# does not match its "name": the app would skip or misname it.
for f in *.json; do
    python3 - "$f" <<'EOF' || exit 1
import json, re, sys
f = sys.argv[1]
d = json.load(open(f))
n = d.get("name", "")
if f != n + ".json" or not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", n):
    sys.exit(f"ERROR: {f}: name {n!r} must match the file name")
EOF
done

%install
install -dm 0755 %{buildroot}%{profdir}
install -pm 0666 *.json %{buildroot}%{profdir}/

%files
# The directory itself belongs to bootsmith (0777, owner bootsmith): the app
# saves a preset by writing a temp file and renaming it over the old one, which
# needs write access to the directory, not the file. 0666 lets operators edit
# a preset in place without root.
%config %attr(0666,root,root) %{profdir}/*.json

%changelog
* Wed Oct 14 2026 Hawi Stecher <hawi.stecher@noirlab.edu> - 1.0.0-1
- Package the presets for the gemini-rtsw-ci pipeline, so a boot server
  takes new presets by installing an RPM.
