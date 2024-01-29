import {ColorName} from './ColorName';
import {CoreColors} from './CoreColors';
import {DataVizColors} from './DataVizColors';
import {TranslucentColors} from './TranslucentColors';

export const LightPalette = {
  [ColorName.BrowserColorScheme]: 'light',
  [ColorName.KeylineDefault]: TranslucentColors.Gray15,
  [ColorName.LinkDefault]: CoreColors.Blue700,
  [ColorName.LinkHover]: CoreColors.Blue500,
  [ColorName.LinkDisabled]: CoreColors.Gray150,
  [ColorName.TextDefault]: CoreColors.Gray990,
  [ColorName.TextLight]: CoreColors.Gray700,
  [ColorName.TextLighter]: CoreColors.Gray500,
  [ColorName.TextDisabled]: CoreColors.Gray400,
  [ColorName.TextRed]: CoreColors.Red700,
  [ColorName.TextYellow]: CoreColors.Yellow700,
  [ColorName.TextGreen]: CoreColors.Green700,
  [ColorName.TextBlue]: CoreColors.Blue700,
  [ColorName.TextOlive]: CoreColors.Olive700,
  [ColorName.TextCyan]: CoreColors.Cyan700,
  [ColorName.TextLime]: CoreColors.Lime700,
  [ColorName.BackgroundDefault]: CoreColors.White,
  [ColorName.BackgroundDefaultHover]: CoreColors.Gray10,
  [ColorName.BackgroundLight]: CoreColors.Gray10,
  [ColorName.BackgroundLightHover]: CoreColors.Gray50,
  [ColorName.BackgroundLighter]: CoreColors.Gray50,
  [ColorName.BackgroundLighterHover]: CoreColors.Gray100,
  [ColorName.BackgroundDisabled]: CoreColors.Gray150,
  [ColorName.BackgroundRed]: TranslucentColors.Red12,
  [ColorName.BackgroundRedHover]: TranslucentColors.Red15,
  [ColorName.BackgroundYellow]: TranslucentColors.Yellow12,
  [ColorName.BackgroundYellowHover]: TranslucentColors.Yellow15,
  [ColorName.BackgroundGreen]: TranslucentColors.Green12,
  [ColorName.BackgroundGreenHover]: TranslucentColors.Green15,
  [ColorName.BackgroundBlue]: TranslucentColors.Blue12,
  [ColorName.BackgroundBlueHover]: TranslucentColors.Blue15,
  [ColorName.BackgroundOlive]: TranslucentColors.Olive12,
  [ColorName.BackgroundOliverHover]: TranslucentColors.Olive15,
  [ColorName.BackgroundCyan]: TranslucentColors.Cyan12,
  [ColorName.BackgroundCyanHover]: TranslucentColors.Cyan15,
  [ColorName.BackgroundLime]: TranslucentColors.Lime12,
  [ColorName.BackgroundLimeHover]: TranslucentColors.Lime15,
  [ColorName.BackgroundGray]: TranslucentColors.Gray12,
  [ColorName.BackgroundGrayHover]: TranslucentColors.Gray15,
  [ColorName.BorderDefault]: CoreColors.Gray200,
  [ColorName.BorderHover]: CoreColors.Gray300,
  [ColorName.BorderDisabled]: CoreColors.Gray500,
  [ColorName.FocusRing]: CoreColors.Blue300,
  [ColorName.AccentPrimary]: CoreColors.Gray950,
  [ColorName.AccentPrimaryHover]: CoreColors.Gray800,
  [ColorName.AccentReversed]: CoreColors.Gray10,
  [ColorName.AccentReversedHover]: CoreColors.White,
  [ColorName.AccentRed]: CoreColors.Red500,
  [ColorName.AccentRedHover]: CoreColors.Red400,
  [ColorName.AccentYellow]: CoreColors.Yellow500,
  [ColorName.AccentYellowHover]: CoreColors.Yellow400,
  [ColorName.AccentGreen]: CoreColors.Green500,
  [ColorName.AccentGreenHover]: CoreColors.Green400,
  [ColorName.AccentBlue]: CoreColors.Blue500,
  [ColorName.AccentBlueHover]: CoreColors.Blue400,
  [ColorName.AccentCyan]: CoreColors.Cyan500,
  [ColorName.AccentCyanHover]: CoreColors.Cyan400,
  [ColorName.AccentLime]: CoreColors.Lime500,
  [ColorName.AccentLimeHover]: CoreColors.Lime400,
  [ColorName.AccentLavender]: CoreColors.Blue200,
  [ColorName.AccentLavenderHover]: CoreColors.Blue100,
  [ColorName.AccentOlive]: CoreColors.Olive500,
  [ColorName.AccentOliveHover]: CoreColors.Olive400,
  [ColorName.AccentGray]: CoreColors.Gray500,
  [ColorName.AccentGrayHover]: CoreColors.Gray400,
  [ColorName.AccentWhite]: CoreColors.White,
  [ColorName.DialogBackground]: TranslucentColors.Gray50,
  [ColorName.TooltipBackground]: CoreColors.Gray850,
  [ColorName.TooltipText]: CoreColors.White,
  [ColorName.PopoverBackground]: CoreColors.White,
  [ColorName.PopoverBackgroundHover]: CoreColors.Gray50,
  [ColorName.ShadowDefault]: TranslucentColors.Gray30,

  // Nav
  [ColorName.NavBackground]: CoreColors.Gray990,
  [ColorName.NavText]: CoreColors.Gray400,
  [ColorName.NavTextHover]: CoreColors.Gray300,
  [ColorName.NavTextSelected]: CoreColors.White,
  [ColorName.NavButton]: CoreColors.Gray900,
  [ColorName.NavButtonHover]: CoreColors.Gray850,

  // Lineage Graph
  [ColorName.LineageDots]: TranslucentColors.Gray20,
  [ColorName.LineageEdge]: CoreColors.Gray100,
  [ColorName.LineageEdgeHighlighted]: CoreColors.Gray400,
  [ColorName.LineageGroupNodeBackground]: CoreColors.Gray10,
  [ColorName.LineageGroupNodeBackgroundHover]: CoreColors.Gray50,
  [ColorName.LineageGroupNodeBorder]: CoreColors.Gray50,
  [ColorName.LineageGroupNodeBorderHover]: CoreColors.Gray50,
  [ColorName.LineageGroupBackground]: TranslucentColors.LightWash,
  [ColorName.LineageNodeBackground]: CoreColors.Gray50,
  [ColorName.LineageNodeBackgroundHover]: CoreColors.Gray100,
  [ColorName.LineageNodeBorder]: CoreColors.Gray150,
  [ColorName.LineageNodeBorderHover]: CoreColors.Gray300,
  [ColorName.LineageNodeBorderSelected]: CoreColors.Blue500,

  // Dataviz
  [ColorName.DataVizBlue]: DataVizColors.Blue200,
  [ColorName.DataVizBlueAlt]: DataVizColors.Blue300,
  [ColorName.DataVizBlurple]: DataVizColors.Blurple200,
  [ColorName.DataVizBlurpleAlt]: DataVizColors.Blurple300,
  [ColorName.DataVizBrown]: DataVizColors.Brown200,
  [ColorName.DataVizBrownAlt]: DataVizColors.Brown300,
  [ColorName.DataVizCyan]: DataVizColors.Cyan200,
  [ColorName.DataVizCyanAlt]: DataVizColors.Cyan300,
  [ColorName.DataVizGray]: DataVizColors.Gray200,
  [ColorName.DataVizGrayAlt]: DataVizColors.Gray300,
  [ColorName.DataVizGreen]: DataVizColors.Green200,
  [ColorName.DataVizGreenAlt]: DataVizColors.Green300,
  [ColorName.DataVizLime]: DataVizColors.Lime200,
  [ColorName.DataVizLimeAlt]: DataVizColors.Lime300,
  [ColorName.DataVizOrange]: DataVizColors.Orange200,
  [ColorName.DataVizOrangeAlt]: DataVizColors.Orange300,
  [ColorName.DataVizPink]: DataVizColors.Pink200,
  [ColorName.DataVizPinkAlt]: DataVizColors.Pink300,
  [ColorName.DataVizRed]: DataVizColors.Red200,
  [ColorName.DataVizRedAlt]: DataVizColors.Red300,
  [ColorName.DataVizTeal]: DataVizColors.Teal200,
  [ColorName.DataVizTealAlt]: DataVizColors.Teal300,
  [ColorName.DataVizViolet]: DataVizColors.Violet200,
  [ColorName.DataVizVioletAlt]: DataVizColors.Violet300,
  [ColorName.DataVizYellow]: DataVizColors.Yellow200,
  [ColorName.DataVizYellowAlt]: DataVizColors.Yellow300,
};
