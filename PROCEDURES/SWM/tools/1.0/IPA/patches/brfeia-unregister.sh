#! /bin/sh

# if brfp is not installed, it is normal that we can't unregister BRF-EIA,
# then exit without causing problems (rc=0)

# if brfp is install, then fail if unregisteration fails

rc=0

if [ -f /opt/ericsson/brf/libexec/common/brf-participant-unregister ]
then
    if [ -f /opt/ericsson/brf/libexec/eia/brfeia-apr9010485/etc/Participant.cfg ]
    then
        /opt/ericsson/brf/libexec/common/brf-participant-unregister \
            /opt/ericsson/brf/libexec/eia/brfeia-apr9010485/etc/Participant.cfg
    elif [ -f /opt/ericsson/brf/libexec/eia/brfeia-apr9010485/Participant.cfg ]
    then
        /opt/ericsson/brf/libexec/common/brf-participant-unregister \
            /opt/ericsson/brf/libexec/eia/brfeia-apr9010485/Participant.cfg
    fi

    rc=$?
fi

exit $rc
