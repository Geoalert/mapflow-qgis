<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Labeling" version="3.42.1-Münster" labelsEnabled="0">
  <renderer-v2 referencescale="-1" symbollevels="0" forceraster="0" type="mergedFeatureRenderer" enableorderby="0">
    <renderer-v2 referencescale="-1" symbollevels="0" forceraster="0" type="RuleRenderer" enableorderby="0">
      <rules key="{02d57c35-56ac-4b75-bcbe-9c2e2c23a7d1}">
        <rule key="{f94f9a48-a46e-4ded-888c-a2f2136ae8cc}" label="Residential" filter="&quot;object_type&quot; = 'building' AND &quot;class_id&quot; = 101" symbol="0"/>
        <rule key="{029d76aa-c053-49de-9a3f-1cf933b4c7cc}" label="Housing" filter="&quot;object_type&quot; = 'building' AND &quot;class_id&quot; = 102" symbol="1"/>
        <rule key="{9b70c38c-f042-42f5-95cb-e2ae235d9cf0}" label="Industrial" filter="&quot;object_type&quot; = 'building' AND &quot;class_id&quot; = 103" symbol="2"/>
        <rule key="{c135357c-6bac-4557-9ba6-6448a9f7db4c}" label="Commercial" filter="&quot;object_type&quot; = 'building' AND &quot;class_id&quot; = 104" symbol="3"/>
        <rule key="{3a69ef06-6c21-444b-a88c-471d5269f8ac}" label="Other" filter="&quot;object_type&quot; = 'building' AND &quot;class_id&quot; = 105" symbol="4"/>
        <rule key="{764a7c9b-3826-40b3-85f1-e5d2c6794273}" label="Roads" filter="&quot;object_type&quot; = 'roads'" symbol="5"/>
        <rule key="{dbf037e1-9c9e-4332-8b0e-b4eff90089fc}" label="0 - 5" filter="&quot;object_type&quot; = 'crown' AND &quot;max_height&quot; > 0.000000 AND &quot;max_height&quot; &lt;= 5.000000" symbol="6"/>
        <rule key="{7545973f-439a-49cd-9699-49c517f1ffc6}" label="7 - 9" filter="&quot;object_type&quot; = 'crown' AND &quot;max_height&quot; > 5.000000 AND &quot;max_height&quot; &lt;= 9.000000" symbol="7"/>
        <rule key="{793f6ad5-4466-4d11-9283-11297778bc8b}" label="9 - 12" filter="&quot;object_type&quot; = 'crown' AND &quot;max_height&quot; > 9.000000 AND &quot;max_height&quot; &lt;= 12.000000" symbol="8"/>
        <rule key="{0abd8155-067a-4faf-bea0-4e21c4a73d2d}" label="12 - 17" filter="&quot;object_type&quot; = 'crown' AND &quot;max_height&quot; > 12.000000 AND &quot;max_height&quot; &lt;= 17.000000" symbol="9"/>
        <rule key="{67f4ad3a-ae06-4a34-aa8e-b21d336d7bc1}" label="17+" filter="&quot;object_type&quot; = 'crown' AND  &quot;max_height&quot; > 17.000000" symbol="10"/>
        <rule key="{c51ecbcd-16d1-490b-b7c8-fc580b5fe9e6}" label="00m-04m" filter="&quot;object_type&quot; = 'forest' AND class_id = '00m-04m'" symbol="11"/>
        <rule key="{3ff5a25c-1fb3-4567-bfc9-924cbab42843}" label="04m-10m" filter="&quot;object_type&quot; = 'forest' AND class_id = '04m-10m'" symbol="12"/>
        <rule key="{4c0cea85-0bcb-44e8-9a2a-95db7313e619}" label="10m-99m" filter="&quot;object_type&quot; = 'forest' AND class_id = '10m-99m'" symbol="13"/>
        <rule key="{b41ff1ee-d71f-43b9-895a-cf5f495f9d2f}" label="Water objects (OSM)" filter="object_type = 'waterbodies'" symbol="14"/>
        <rule key="{f8acf346-dae1-4ef8-bf38-ddad804c9cf7}" label="Forest" filter="&quot;object_type&quot; = 'forest'" symbol="15"/>
        <rule key="{2198293c-f9cc-4763-ab84-4b5c960984d8}" filter="ELSE" symbol="16"/>
      </rules>
      <symbols>
        <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="0" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" id="{9a368e3c-f956-49f9-8fe7-4d76ad35feb6}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="228,26,28,191,rgb:0.89411764705882357,0.10196078431372549,0.10980392156862745,0.74901960784313726" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="128,14,16,255,rgb:0.50196078431372548,0.05490196078431372,0.06274509803921569,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.66" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="solid" name="style" type="QString"/>
            </Option>
            <effect enabled="0" type="effectStack">
              <effect type="dropShadow">
                <Option type="Map">
                  <Option value="13" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,0,255,rgb:0,0,0,1" name="color" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="135" name="offset_angle" type="QString"/>
                  <Option value="2" name="offset_distance" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_unit_scale" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="outerGlow">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="0.7935" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,255,255,rgb:0,0,1,1" name="color1" type="QString"/>
                  <Option value="0,255,0,255,rgb:0,1,0,1" name="color2" type="QString"/>
                  <Option value="0" name="color_type" type="QString"/>
                  <Option value="ccw" name="direction" type="QString"/>
                  <Option value="0" name="discrete" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="0.5" name="opacity" type="QString"/>
                  <Option value="gradient" name="rampType" type="QString"/>
                  <Option value="255,255,255,255,rgb:1,1,1,1" name="single_color" type="QString"/>
                  <Option value="rgb" name="spec" type="QString"/>
                  <Option value="2" name="spread" type="QString"/>
                  <Option value="MM" name="spread_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="spread_unit_scale" type="QString"/>
                </Option>
              </effect>
              <effect type="blur">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="0" name="blur_method" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="1" name="enabled" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="innerShadow">
                <Option type="Map">
                  <Option value="13" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,0,255,rgb:0,0,0,1" name="color" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="135" name="offset_angle" type="QString"/>
                  <Option value="2" name="offset_distance" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_unit_scale" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="innerGlow">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="0.7935" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,255,255,rgb:0,0,1,1" name="color1" type="QString"/>
                  <Option value="0,255,0,255,rgb:0,1,0,1" name="color2" type="QString"/>
                  <Option value="0" name="color_type" type="QString"/>
                  <Option value="ccw" name="direction" type="QString"/>
                  <Option value="0" name="discrete" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="0.5" name="opacity" type="QString"/>
                  <Option value="gradient" name="rampType" type="QString"/>
                  <Option value="255,255,255,255,rgb:1,1,1,1" name="single_color" type="QString"/>
                  <Option value="rgb" name="spec" type="QString"/>
                  <Option value="2" name="spread" type="QString"/>
                  <Option value="MM" name="spread_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="spread_unit_scale" type="QString"/>
                </Option>
              </effect>
            </effect>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="1" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" id="{9260a279-a215-4423-b170-df84411ce245}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="255,153,0,177,rgb:1,0.59999999999999998,0,0.69411764705882351" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="128,14,16,255,rgb:0.50196078431372548,0.05490196078431372,0.06274509803921569,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.66" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="solid" name="style" type="QString"/>
            </Option>
            <effect enabled="0" type="effectStack">
              <effect type="dropShadow">
                <Option type="Map">
                  <Option value="13" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,0,255,rgb:0,0,0,1" name="color" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="135" name="offset_angle" type="QString"/>
                  <Option value="2" name="offset_distance" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_unit_scale" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="outerGlow">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="0.7935" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,255,255,rgb:0,0,1,1" name="color1" type="QString"/>
                  <Option value="0,255,0,255,rgb:0,1,0,1" name="color2" type="QString"/>
                  <Option value="0" name="color_type" type="QString"/>
                  <Option value="ccw" name="direction" type="QString"/>
                  <Option value="0" name="discrete" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="0.5" name="opacity" type="QString"/>
                  <Option value="gradient" name="rampType" type="QString"/>
                  <Option value="255,255,255,255,rgb:1,1,1,1" name="single_color" type="QString"/>
                  <Option value="rgb" name="spec" type="QString"/>
                  <Option value="2" name="spread" type="QString"/>
                  <Option value="MM" name="spread_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="spread_unit_scale" type="QString"/>
                </Option>
              </effect>
              <effect type="blur">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="0" name="blur_method" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="1" name="enabled" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="innerShadow">
                <Option type="Map">
                  <Option value="13" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,0,255,rgb:0,0,0,1" name="color" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="135" name="offset_angle" type="QString"/>
                  <Option value="2" name="offset_distance" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_unit_scale" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="innerGlow">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="0.7935" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,255,255,rgb:0,0,1,1" name="color1" type="QString"/>
                  <Option value="0,255,0,255,rgb:0,1,0,1" name="color2" type="QString"/>
                  <Option value="0" name="color_type" type="QString"/>
                  <Option value="ccw" name="direction" type="QString"/>
                  <Option value="0" name="discrete" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="0.5" name="opacity" type="QString"/>
                  <Option value="gradient" name="rampType" type="QString"/>
                  <Option value="255,255,255,255,rgb:1,1,1,1" name="single_color" type="QString"/>
                  <Option value="rgb" name="spec" type="QString"/>
                  <Option value="2" name="spread" type="QString"/>
                  <Option value="MM" name="spread_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="spread_unit_scale" type="QString"/>
                </Option>
              </effect>
            </effect>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="0.7" clip_to_extent="1" is_animated="0" force_rhr="0" name="10" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="2" id="{27df9678-dd3c-4bd2-b626-b9e75b736878}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="243,236,100,255,rgb:0.95294117647058818,0.92549019607843142,0.39215686274509803,1" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="56,128,54,255,rgb:0.2196078431372549,0.50196078431372548,0.21176470588235294,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.26" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="solid" name="style" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="11" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="1" id="{72fa1f9e-9a26-4b4f-8d0b-11cdcaa38b61}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="48,115,247,179,rgb:0.18823529411764706,0.45098039215686275,0.96862745098039216,0.70196078431372544" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="0,41,247,255,rgb:0,0.16078431372549021,0.96862745098039216,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.26" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="dense3" name="style" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="12" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="1" id="{c18e8e4e-8a7a-4df5-8f28-4321ced75d4c}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="103,186,101,204,rgb:0.40392156862745099,0.72941176470588232,0.396078431372549,0.80000000000000004" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="76,161,82,255,rgb:0.29803921568627451,0.63137254901960782,0.32156862745098042,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.26" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="dense3" name="style" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="13" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="1" id="{20461288-5c4a-4908-b5b0-33bfd64b0750}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="255,202,66,255,rgb:1,0.792156862745098,0.25882352941176473,1" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="247,146,0,255,rgb:0.96862745098039216,0.5725490196078431,0,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.26" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="dense3" name="style" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="14" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" id="{9041fcd3-244e-40c6-9842-cdc0c18ee9d5}" enabled="1" locked="0" class="LinePatternFill">
            <Option type="Map">
              <Option value="135" name="angle" type="QString"/>
              <Option value="during_render" name="clip_mode" type="QString"/>
              <Option value="11,0,255,255,rgb:0.0417792019531548,0,1,1" name="color" type="QString"/>
              <Option value="feature" name="coordinate_reference" type="QString"/>
              <Option value="2" name="distance" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="distance_map_unit_scale" type="QString"/>
              <Option value="MM" name="distance_unit" type="QString"/>
              <Option value="0.26" name="line_width" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="line_width_map_unit_scale" type="QString"/>
              <Option value="MM" name="line_width_unit" type="QString"/>
              <Option value="0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
            <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="@14@0" frame_rate="10" type="line">
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
              <layer pass="0" id="{7bf86bb4-e55a-48ff-8af2-e91610cf0501}" enabled="1" locked="0" class="SimpleLine">
                <Option type="Map">
                  <Option value="0" name="align_dash_pattern" type="QString"/>
                  <Option value="square" name="capstyle" type="QString"/>
                  <Option value="5;2" name="customdash" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="customdash_map_unit_scale" type="QString"/>
                  <Option value="MM" name="customdash_unit" type="QString"/>
                  <Option value="0" name="dash_pattern_offset" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="dash_pattern_offset_map_unit_scale" type="QString"/>
                  <Option value="MM" name="dash_pattern_offset_unit" type="QString"/>
                  <Option value="0" name="draw_inside_polygon" type="QString"/>
                  <Option value="bevel" name="joinstyle" type="QString"/>
                  <Option value="11,0,255,255,rgb:0.0417792019531548,0,1,1" name="line_color" type="QString"/>
                  <Option value="solid" name="line_style" type="QString"/>
                  <Option value="0.3" name="line_width" type="QString"/>
                  <Option value="MM" name="line_width_unit" type="QString"/>
                  <Option value="0" name="offset" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="0" name="ring_filter" type="QString"/>
                  <Option value="0" name="trim_distance_end" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="trim_distance_end_map_unit_scale" type="QString"/>
                  <Option value="MM" name="trim_distance_end_unit" type="QString"/>
                  <Option value="0" name="trim_distance_start" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="trim_distance_start_map_unit_scale" type="QString"/>
                  <Option value="MM" name="trim_distance_start_unit" type="QString"/>
                  <Option value="0" name="tweak_dash_pattern_on_corners" type="QString"/>
                  <Option value="0" name="use_custom_dash" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="width_map_unit_scale" type="QString"/>
                </Option>
                <data_defined_properties>
                  <Option type="Map">
                    <Option value="" name="name" type="QString"/>
                    <Option name="properties"/>
                    <Option value="collection" name="type" type="QString"/>
                  </Option>
                </data_defined_properties>
              </layer>
            </symbol>
          </layer>
          <layer pass="0" id="{8487ba09-71d2-4bba-a69d-17ca89a89842}" enabled="1" locked="0" class="SimpleLine">
            <Option type="Map">
              <Option value="0" name="align_dash_pattern" type="QString"/>
              <Option value="square" name="capstyle" type="QString"/>
              <Option value="5;2" name="customdash" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="customdash_map_unit_scale" type="QString"/>
              <Option value="MM" name="customdash_unit" type="QString"/>
              <Option value="0" name="dash_pattern_offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="dash_pattern_offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="dash_pattern_offset_unit" type="QString"/>
              <Option value="0" name="draw_inside_polygon" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="11,0,255,255,rgb:0.0417792019531548,0,1,1" name="line_color" type="QString"/>
              <Option value="solid" name="line_style" type="QString"/>
              <Option value="0.46" name="line_width" type="QString"/>
              <Option value="MM" name="line_width_unit" type="QString"/>
              <Option value="0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="0" name="ring_filter" type="QString"/>
              <Option value="0" name="trim_distance_end" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="trim_distance_end_map_unit_scale" type="QString"/>
              <Option value="MM" name="trim_distance_end_unit" type="QString"/>
              <Option value="0" name="trim_distance_start" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="trim_distance_start_map_unit_scale" type="QString"/>
              <Option value="MM" name="trim_distance_start_unit" type="QString"/>
              <Option value="0" name="tweak_dash_pattern_on_corners" type="QString"/>
              <Option value="0" name="use_custom_dash" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="width_map_unit_scale" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="15" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" id="{f77e7832-49b7-4d23-983d-787037525fd3}" enabled="1" locked="0" class="LinePatternFill">
            <Option type="Map">
              <Option value="135" name="angle" type="QString"/>
              <Option value="during_render" name="clip_mode" type="QString"/>
              <Option value="16,218,10,255,rgb:0.06274509803921569,0.85490196078431369,0.0392156862745098,1" name="color" type="QString"/>
              <Option value="feature" name="coordinate_reference" type="QString"/>
              <Option value="2" name="distance" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="distance_map_unit_scale" type="QString"/>
              <Option value="MM" name="distance_unit" type="QString"/>
              <Option value="0.26" name="line_width" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="line_width_map_unit_scale" type="QString"/>
              <Option value="MM" name="line_width_unit" type="QString"/>
              <Option value="0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="outline_width_map_unit_scale" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
            <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="@15@0" frame_rate="10" type="line">
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
              <layer pass="0" id="{e26ad4a3-140e-481f-b80b-38725ca3228e}" enabled="1" locked="0" class="SimpleLine">
                <Option type="Map">
                  <Option value="0" name="align_dash_pattern" type="QString"/>
                  <Option value="square" name="capstyle" type="QString"/>
                  <Option value="5;2" name="customdash" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="customdash_map_unit_scale" type="QString"/>
                  <Option value="MM" name="customdash_unit" type="QString"/>
                  <Option value="0" name="dash_pattern_offset" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="dash_pattern_offset_map_unit_scale" type="QString"/>
                  <Option value="MM" name="dash_pattern_offset_unit" type="QString"/>
                  <Option value="0" name="draw_inside_polygon" type="QString"/>
                  <Option value="bevel" name="joinstyle" type="QString"/>
                  <Option value="16,218,10,255,rgb:0.06274509803921569,0.85490196078431369,0.0392156862745098,1" name="line_color" type="QString"/>
                  <Option value="solid" name="line_style" type="QString"/>
                  <Option value="0.5" name="line_width" type="QString"/>
                  <Option value="MM" name="line_width_unit" type="QString"/>
                  <Option value="0" name="offset" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="0" name="ring_filter" type="QString"/>
                  <Option value="0" name="trim_distance_end" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="trim_distance_end_map_unit_scale" type="QString"/>
                  <Option value="MM" name="trim_distance_end_unit" type="QString"/>
                  <Option value="0" name="trim_distance_start" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="trim_distance_start_map_unit_scale" type="QString"/>
                  <Option value="MM" name="trim_distance_start_unit" type="QString"/>
                  <Option value="0" name="tweak_dash_pattern_on_corners" type="QString"/>
                  <Option value="0" name="use_custom_dash" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="width_map_unit_scale" type="QString"/>
                </Option>
                <data_defined_properties>
                  <Option type="Map">
                    <Option value="" name="name" type="QString"/>
                    <Option name="properties"/>
                    <Option value="collection" name="type" type="QString"/>
                  </Option>
                </data_defined_properties>
              </layer>
            </symbol>
          </layer>
          <layer pass="0" id="{e873226a-3029-4d1e-a8fe-cc5a6da388bc}" enabled="1" locked="0" class="SimpleLine">
            <Option type="Map">
              <Option value="0" name="align_dash_pattern" type="QString"/>
              <Option value="square" name="capstyle" type="QString"/>
              <Option value="5;2" name="customdash" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="customdash_map_unit_scale" type="QString"/>
              <Option value="MM" name="customdash_unit" type="QString"/>
              <Option value="0" name="dash_pattern_offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="dash_pattern_offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="dash_pattern_offset_unit" type="QString"/>
              <Option value="0" name="draw_inside_polygon" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="16,218,10,255,rgb:0.06274509803921569,0.85490196078431369,0.0392156862745098,1" name="line_color" type="QString"/>
              <Option value="solid" name="line_style" type="QString"/>
              <Option value="0.46" name="line_width" type="QString"/>
              <Option value="MM" name="line_width_unit" type="QString"/>
              <Option value="0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="0" name="ring_filter" type="QString"/>
              <Option value="0" name="trim_distance_end" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="trim_distance_end_map_unit_scale" type="QString"/>
              <Option value="MM" name="trim_distance_end_unit" type="QString"/>
              <Option value="0" name="trim_distance_start" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="trim_distance_start_map_unit_scale" type="QString"/>
              <Option value="MM" name="trim_distance_start_unit" type="QString"/>
              <Option value="0" name="tweak_dash_pattern_on_corners" type="QString"/>
              <Option value="0" name="use_custom_dash" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="width_map_unit_scale" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="16" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" id="{6cfafd3b-8b86-49f8-af93-e7ed3158db53}" enabled="1" locked="0" class="SimpleLine">
            <Option type="Map">
              <Option value="0" name="align_dash_pattern" type="QString"/>
              <Option value="square" name="capstyle" type="QString"/>
              <Option value="5;2" name="customdash" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="customdash_map_unit_scale" type="QString"/>
              <Option value="MM" name="customdash_unit" type="QString"/>
              <Option value="0" name="dash_pattern_offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="dash_pattern_offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="dash_pattern_offset_unit" type="QString"/>
              <Option value="0" name="draw_inside_polygon" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="43,131,186,255,rgb:0.16862745098039217,0.51372549019607838,0.72941176470588232,1" name="line_color" type="QString"/>
              <Option value="solid" name="line_style" type="QString"/>
              <Option value="0.76" name="line_width" type="QString"/>
              <Option value="MM" name="line_width_unit" type="QString"/>
              <Option value="0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="0" name="ring_filter" type="QString"/>
              <Option value="0" name="trim_distance_end" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="trim_distance_end_map_unit_scale" type="QString"/>
              <Option value="MM" name="trim_distance_end_unit" type="QString"/>
              <Option value="0" name="trim_distance_start" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="trim_distance_start_map_unit_scale" type="QString"/>
              <Option value="MM" name="trim_distance_start_unit" type="QString"/>
              <Option value="0" name="tweak_dash_pattern_on_corners" type="QString"/>
              <Option value="0" name="use_custom_dash" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="width_map_unit_scale" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="2" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" id="{41a5089e-59a8-4adf-8731-f6e5f1561e4e}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="255,0,251,167,rgb:1,0,0.98431372549019602,0.65490196078431373" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="128,14,16,255,rgb:0.50196078431372548,0.05490196078431372,0.06274509803921569,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.66" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="solid" name="style" type="QString"/>
            </Option>
            <effect enabled="0" type="effectStack">
              <effect type="dropShadow">
                <Option type="Map">
                  <Option value="13" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,0,255,rgb:0,0,0,1" name="color" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="135" name="offset_angle" type="QString"/>
                  <Option value="2" name="offset_distance" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_unit_scale" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="outerGlow">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="0.7935" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,255,255,rgb:0,0,1,1" name="color1" type="QString"/>
                  <Option value="0,255,0,255,rgb:0,1,0,1" name="color2" type="QString"/>
                  <Option value="0" name="color_type" type="QString"/>
                  <Option value="ccw" name="direction" type="QString"/>
                  <Option value="0" name="discrete" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="0.5" name="opacity" type="QString"/>
                  <Option value="gradient" name="rampType" type="QString"/>
                  <Option value="255,255,255,255,rgb:1,1,1,1" name="single_color" type="QString"/>
                  <Option value="rgb" name="spec" type="QString"/>
                  <Option value="2" name="spread" type="QString"/>
                  <Option value="MM" name="spread_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="spread_unit_scale" type="QString"/>
                </Option>
              </effect>
              <effect type="blur">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="0" name="blur_method" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="1" name="enabled" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="innerShadow">
                <Option type="Map">
                  <Option value="13" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,0,255,rgb:0,0,0,1" name="color" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="135" name="offset_angle" type="QString"/>
                  <Option value="2" name="offset_distance" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_unit_scale" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="innerGlow">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="0.7935" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,255,255,rgb:0,0,1,1" name="color1" type="QString"/>
                  <Option value="0,255,0,255,rgb:0,1,0,1" name="color2" type="QString"/>
                  <Option value="0" name="color_type" type="QString"/>
                  <Option value="ccw" name="direction" type="QString"/>
                  <Option value="0" name="discrete" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="0.5" name="opacity" type="QString"/>
                  <Option value="gradient" name="rampType" type="QString"/>
                  <Option value="255,255,255,255,rgb:1,1,1,1" name="single_color" type="QString"/>
                  <Option value="rgb" name="spec" type="QString"/>
                  <Option value="2" name="spread" type="QString"/>
                  <Option value="MM" name="spread_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="spread_unit_scale" type="QString"/>
                </Option>
              </effect>
            </effect>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="3" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" id="{5288b3a2-6829-4376-94c8-f2ab5b1d8f64}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="29,255,232,179,rgb:0.11372549019607843,1,0.90980392156862744,0.70196078431372544" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="128,14,16,255,rgb:0.50196078431372548,0.05490196078431372,0.06274509803921569,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.66" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="solid" name="style" type="QString"/>
            </Option>
            <effect enabled="0" type="effectStack">
              <effect type="dropShadow">
                <Option type="Map">
                  <Option value="13" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,0,255,rgb:0,0,0,1" name="color" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="135" name="offset_angle" type="QString"/>
                  <Option value="2" name="offset_distance" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_unit_scale" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="outerGlow">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="0.7935" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,255,255,rgb:0,0,1,1" name="color1" type="QString"/>
                  <Option value="0,255,0,255,rgb:0,1,0,1" name="color2" type="QString"/>
                  <Option value="0" name="color_type" type="QString"/>
                  <Option value="ccw" name="direction" type="QString"/>
                  <Option value="0" name="discrete" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="0.5" name="opacity" type="QString"/>
                  <Option value="gradient" name="rampType" type="QString"/>
                  <Option value="255,255,255,255,rgb:1,1,1,1" name="single_color" type="QString"/>
                  <Option value="rgb" name="spec" type="QString"/>
                  <Option value="2" name="spread" type="QString"/>
                  <Option value="MM" name="spread_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="spread_unit_scale" type="QString"/>
                </Option>
              </effect>
              <effect type="blur">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="0" name="blur_method" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="1" name="enabled" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="innerShadow">
                <Option type="Map">
                  <Option value="13" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,0,255,rgb:0,0,0,1" name="color" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="135" name="offset_angle" type="QString"/>
                  <Option value="2" name="offset_distance" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_unit_scale" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="innerGlow">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="0.7935" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,255,255,rgb:0,0,1,1" name="color1" type="QString"/>
                  <Option value="0,255,0,255,rgb:0,1,0,1" name="color2" type="QString"/>
                  <Option value="0" name="color_type" type="QString"/>
                  <Option value="ccw" name="direction" type="QString"/>
                  <Option value="0" name="discrete" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="0.5" name="opacity" type="QString"/>
                  <Option value="gradient" name="rampType" type="QString"/>
                  <Option value="255,255,255,255,rgb:1,1,1,1" name="single_color" type="QString"/>
                  <Option value="rgb" name="spec" type="QString"/>
                  <Option value="2" name="spread" type="QString"/>
                  <Option value="MM" name="spread_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="spread_unit_scale" type="QString"/>
                </Option>
              </effect>
            </effect>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="4" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" id="{80e8931a-a34f-4160-b345-12bcff7acad0}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="29,59,255,165,rgb:0.11372549019607843,0.23137254901960785,1,0.6470588235294118" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="128,14,16,255,rgb:0.50196078431372548,0.05490196078431372,0.06274509803921569,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.66" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="solid" name="style" type="QString"/>
            </Option>
            <effect enabled="0" type="effectStack">
              <effect type="dropShadow">
                <Option type="Map">
                  <Option value="13" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,0,255,rgb:0,0,0,1" name="color" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="135" name="offset_angle" type="QString"/>
                  <Option value="2" name="offset_distance" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_unit_scale" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="outerGlow">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="0.7935" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,255,255,rgb:0,0,1,1" name="color1" type="QString"/>
                  <Option value="0,255,0,255,rgb:0,1,0,1" name="color2" type="QString"/>
                  <Option value="0" name="color_type" type="QString"/>
                  <Option value="ccw" name="direction" type="QString"/>
                  <Option value="0" name="discrete" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="0.5" name="opacity" type="QString"/>
                  <Option value="gradient" name="rampType" type="QString"/>
                  <Option value="255,255,255,255,rgb:1,1,1,1" name="single_color" type="QString"/>
                  <Option value="rgb" name="spec" type="QString"/>
                  <Option value="2" name="spread" type="QString"/>
                  <Option value="MM" name="spread_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="spread_unit_scale" type="QString"/>
                </Option>
              </effect>
              <effect type="blur">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="0" name="blur_method" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="1" name="enabled" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="innerShadow">
                <Option type="Map">
                  <Option value="13" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,0,255,rgb:0,0,0,1" name="color" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="135" name="offset_angle" type="QString"/>
                  <Option value="2" name="offset_distance" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_unit_scale" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="innerGlow">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="0.7935" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,255,255,rgb:0,0,1,1" name="color1" type="QString"/>
                  <Option value="0,255,0,255,rgb:0,1,0,1" name="color2" type="QString"/>
                  <Option value="0" name="color_type" type="QString"/>
                  <Option value="ccw" name="direction" type="QString"/>
                  <Option value="0" name="discrete" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="0.5" name="opacity" type="QString"/>
                  <Option value="gradient" name="rampType" type="QString"/>
                  <Option value="255,255,255,255,rgb:1,1,1,1" name="single_color" type="QString"/>
                  <Option value="rgb" name="spec" type="QString"/>
                  <Option value="2" name="spread" type="QString"/>
                  <Option value="MM" name="spread_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="spread_unit_scale" type="QString"/>
                </Option>
              </effect>
            </effect>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="0.802" clip_to_extent="1" is_animated="0" force_rhr="0" name="5" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" id="{69c7a420-08ca-49a4-b3e0-054946ea86d9}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="228,114,26,255,rgb:0.89411764705882357,0.44705882352941179,0.10196078431372549,1" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="128,14,16,255,rgb:0.50196078431372548,0.05490196078431372,0.06274509803921569,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.6" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="solid" name="style" type="QString"/>
            </Option>
            <effect enabled="0" type="effectStack">
              <effect type="dropShadow">
                <Option type="Map">
                  <Option value="13" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,0,255,rgb:0,0,0,1" name="color" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="135" name="offset_angle" type="QString"/>
                  <Option value="2" name="offset_distance" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_unit_scale" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="outerGlow">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="0.7935" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,255,255,rgb:0,0,1,1" name="color1" type="QString"/>
                  <Option value="0,255,0,255,rgb:0,1,0,1" name="color2" type="QString"/>
                  <Option value="0" name="color_type" type="QString"/>
                  <Option value="ccw" name="direction" type="QString"/>
                  <Option value="0" name="discrete" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="0.5" name="opacity" type="QString"/>
                  <Option value="gradient" name="rampType" type="QString"/>
                  <Option value="255,255,255,255,rgb:1,1,1,1" name="single_color" type="QString"/>
                  <Option value="rgb" name="spec" type="QString"/>
                  <Option value="2" name="spread" type="QString"/>
                  <Option value="MM" name="spread_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="spread_unit_scale" type="QString"/>
                </Option>
              </effect>
              <effect type="blur">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="0" name="blur_method" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="1" name="enabled" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="innerShadow">
                <Option type="Map">
                  <Option value="13" name="blend_mode" type="QString"/>
                  <Option value="2.645" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,0,255,rgb:0,0,0,1" name="color" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="135" name="offset_angle" type="QString"/>
                  <Option value="2" name="offset_distance" type="QString"/>
                  <Option value="MM" name="offset_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="offset_unit_scale" type="QString"/>
                  <Option value="1" name="opacity" type="QString"/>
                </Option>
              </effect>
              <effect type="innerGlow">
                <Option type="Map">
                  <Option value="0" name="blend_mode" type="QString"/>
                  <Option value="0.7935" name="blur_level" type="QString"/>
                  <Option value="MM" name="blur_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="blur_unit_scale" type="QString"/>
                  <Option value="0,0,255,255,rgb:0,0,1,1" name="color1" type="QString"/>
                  <Option value="0,255,0,255,rgb:0,1,0,1" name="color2" type="QString"/>
                  <Option value="0" name="color_type" type="QString"/>
                  <Option value="ccw" name="direction" type="QString"/>
                  <Option value="0" name="discrete" type="QString"/>
                  <Option value="2" name="draw_mode" type="QString"/>
                  <Option value="0" name="enabled" type="QString"/>
                  <Option value="0.5" name="opacity" type="QString"/>
                  <Option value="gradient" name="rampType" type="QString"/>
                  <Option value="255,255,255,255,rgb:1,1,1,1" name="single_color" type="QString"/>
                  <Option value="rgb" name="spec" type="QString"/>
                  <Option value="2" name="spread" type="QString"/>
                  <Option value="MM" name="spread_unit" type="QString"/>
                  <Option value="3x:0,0,0,0,0,0" name="spread_unit_scale" type="QString"/>
                </Option>
              </effect>
            </effect>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="0.7" clip_to_extent="1" is_animated="0" force_rhr="0" name="6" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="2" id="{19e6d06b-35ac-46cf-9377-2a24f6f6814b}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="59,133,139,255,rgb:0.23137254901960785,0.52156862745098043,0.54509803921568623,1" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.26" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="solid" name="style" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="0.7" clip_to_extent="1" is_animated="0" force_rhr="0" name="7" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="2" id="{e059f018-14b4-443b-be20-88aada260420}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="60,164,117,255,rgb:0.23529411764705882,0.64313725490196083,0.45882352941176469,1" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.26" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="solid" name="style" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="0.7" clip_to_extent="1" is_animated="0" force_rhr="0" name="8" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="2" id="{1f20b06e-9351-48bc-ad30-ba423714722d}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="101,219,107,255,rgb:0.396078431372549,0.85882352941176465,0.41960784313725491,1" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.26" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="solid" name="style" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
        <symbol alpha="0.7" clip_to_extent="1" is_animated="0" force_rhr="0" name="9" frame_rate="10" type="fill">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <layer pass="2" id="{e4e55bfb-8c55-4cc5-87a7-bb0db2e69306}" enabled="1" locked="0" class="SimpleFill">
            <Option type="Map">
              <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
              <Option value="188,231,37,255,rgb:0.73725490196078436,0.90588235294117647,0.14509803921568629,1" name="color" type="QString"/>
              <Option value="bevel" name="joinstyle" type="QString"/>
              <Option value="0,0" name="offset" type="QString"/>
              <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
              <Option value="MM" name="offset_unit" type="QString"/>
              <Option value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" name="outline_color" type="QString"/>
              <Option value="solid" name="outline_style" type="QString"/>
              <Option value="0.26" name="outline_width" type="QString"/>
              <Option value="MM" name="outline_width_unit" type="QString"/>
              <Option value="solid" name="style" type="QString"/>
            </Option>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" name="name" type="QString"/>
                <Option name="properties"/>
                <Option value="collection" name="type" type="QString"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </symbols>
      <data-defined-properties>
        <Option type="Map">
          <Option value="" name="name" type="QString"/>
          <Option name="properties"/>
          <Option value="collection" name="type" type="QString"/>
        </Option>
      </data-defined-properties>
    </renderer-v2>
    <data-defined-properties>
      <Option type="Map">
        <Option value="" name="name" type="QString"/>
        <Option name="properties"/>
        <Option value="collection" name="type" type="QString"/>
      </Option>
    </data-defined-properties>
  </renderer-v2>
  <selection mode="Default">
    <selectionColor invalid="1"/>
    <selectionSymbol>
      <symbol alpha="1" clip_to_extent="1" is_animated="0" force_rhr="0" name="" frame_rate="10" type="fill">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" name="name" type="QString"/>
            <Option name="properties"/>
            <Option value="collection" name="type" type="QString"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" id="{75961895-cdca-4c2e-988b-f1e46c7e65df}" enabled="1" locked="0" class="SimpleFill">
          <Option type="Map">
            <Option value="3x:0,0,0,0,0,0" name="border_width_map_unit_scale" type="QString"/>
            <Option value="0,0,255,255,rgb:0,0,1,1" name="color" type="QString"/>
            <Option value="bevel" name="joinstyle" type="QString"/>
            <Option value="0,0" name="offset" type="QString"/>
            <Option value="3x:0,0,0,0,0,0" name="offset_map_unit_scale" type="QString"/>
            <Option value="MM" name="offset_unit" type="QString"/>
            <Option value="35,35,35,255,rgb:0.13725490196078433,0.13725490196078433,0.13725490196078433,1" name="outline_color" type="QString"/>
            <Option value="solid" name="outline_style" type="QString"/>
            <Option value="0.26" name="outline_width" type="QString"/>
            <Option value="MM" name="outline_width_unit" type="QString"/>
            <Option value="solid" name="style" type="QString"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </selectionSymbol>
  </selection>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>2</layerGeometryType>
</qgis>
