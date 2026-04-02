from gws_core import (
    AppConfig,
    AppType,
    ConfigParams,
    ConfigSpecs,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    ReflexResource,
    Task,
    TaskInputs,
    TaskOutputs,
    app_decorator,
    task_decorator,
)


@app_decorator("CareAppConfig", app_type=AppType.REFLEX,
               human_name="Care app")
class CareAppConfig(AppConfig):
    """App configuration for the gws_care Reflex application."""

    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(__file__, "_care_app")


@task_decorator("GenerateCareApp", human_name="Generate Care app",
                style=ReflexResource.copy_style())
class GenerateCareApp(Task):
    """Task that generates the Care app."""

    input_specs = InputSpecs()
    output_specs = OutputSpecs({
        'reflex_app': OutputSpec(ReflexResource)
    })

    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        reflex_app = ReflexResource()
        reflex_app.set_app_config(CareAppConfig())
        reflex_app.name = "Care"
        return {"reflex_app": reflex_app}
