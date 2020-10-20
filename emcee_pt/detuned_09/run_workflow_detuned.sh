set -e
WORKFLOW_NAME=detuned_emceept_relative_09
# Set the HTML_DIR to point to your public html page. This is where the results
# page will be written.
HTML_DIR='/work/stephanie.brown/WWW/cosmic_explorer/'
if [ "${HTML_DIR}" == '' ]; then
    echo "Please set an HTML_DIR"
    exit 1
fi
SEED=983124
# Set the number of injections to create. For a full PP test, we suggest using
# 100.
NINJ=1
pycbc_make_inference_inj_workflow \
    --seed ${SEED} \
    --config-files workflow_config.ini detuned_injections_config.ini\
    --workflow-name ${WORKFLOW_NAME} \
    --injection-file  injection.hdf \
    --config-overrides results_page:output-path:${HTML_DIR}/${WORKFLOW_NAME}
