using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Effects;
using System.Windows.Shapes;

namespace BSLabTool.UI.Views
{
    public partial class VisualTestPointWindow : Window
    {
        private readonly Dictionary<string, JsonElement> _allTestPoints = new(StringComparer.OrdinalIgnoreCase);
        private string _activeBrandFilter = "ALL";
        private double _zoomFactor = 1.0;

        public VisualTestPointWindow()
        {
            InitializeComponent();
            LoadTestPointsDatabase();
        }

        private void OnTitleBarMouseDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Left) DragMove();
        }

        private void OnCloseClicked(object sender, RoutedEventArgs e)
        {
            Close();
        }

        private void LoadTestPointsDatabase()
        {
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string jsonPath = System.IO.Path.Combine(baseDir, "resources", "database", "testpoints_database.json");
                if (!File.Exists(jsonPath))
                {
                    jsonPath = @"C:\BSLab_Tool\resources\database\testpoints_database.json";
                }

                if (File.Exists(jsonPath))
                {
                    string json = File.ReadAllText(jsonPath);
                    using var doc = JsonDocument.Parse(json);
                    foreach (var prop in doc.RootElement.EnumerateObject())
                    {
                        _allTestPoints[prop.Name] = prop.Value.Clone();
                    }
                }

                ApplyFilters();

                // Select first model if available
                if (LstModels.Items.Count > 0)
                {
                    LstModels.SelectedIndex = 0;
                }
            }
            catch (Exception ex)
            {
                TxtDetailInstructions.Text = $"Failed to load test point database: {ex.Message}";
            }
        }

        private void ApplyFilters()
        {
            string query = TxtSearch?.Text?.Trim().ToLowerInvariant() ?? "";
            var filtered = _allTestPoints.Where(kvp =>
            {
                var el = kvp.Value;
                string brand = el.TryGetProperty("brand", out var b) ? b.GetString() ?? "" : "";
                if (_activeBrandFilter != "ALL" && !brand.Equals(_activeBrandFilter, StringComparison.OrdinalIgnoreCase))
                {
                    return false;
                }

                if (string.IsNullOrEmpty(query)) return true;

                string name = kvp.Key.ToLowerInvariant();
                string chipset = el.TryGetProperty("chipset", out var c) ? c.GetString()?.ToLowerInvariant() ?? "" : "";
                string mode = el.TryGetProperty("mode", out var m) ? m.GetString()?.ToLowerInvariant() ?? "" : "";

                return name.Contains(query) || brand.ToLowerInvariant().Contains(query) || chipset.Contains(query) || mode.Contains(query);
            }).ToList();

            LstModels.ItemsSource = filtered;
        }

        private void OnSearchTextChanged(object sender, TextChangedEventArgs e)
        {
            ApplyFilters();
        }

        private void OnBrandFilterClicked(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string brandTag)
            {
                _activeBrandFilter = brandTag;
                ApplyFilters();
            }
        }

        private void OnModelSelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (LstModels.SelectedItem is KeyValuePair<string, JsonElement> selected)
            {
                RenderModelTestPoint(selected.Key, selected.Value);
            }
        }

        private void RenderModelTestPoint(string modelName, JsonElement data)
        {
            TxtCanvasModelTitle.Text = $"📍 PCB SCHEMATIC: {modelName}";
            TxtDetailModelName.Text = modelName;
            TxtDetailChipset.Text = data.TryGetProperty("chipset", out var cs) ? cs.GetString() : "Generic Chipset";
            TxtDetailMode.Text = data.TryGetProperty("mode", out var md) ? md.GetString() : "TestPoint Mode";
            TxtDetailDifficulty.Text = data.TryGetProperty("difficulty", out var df) ? df.GetString() : "Standard";
            TxtDetailInstructions.Text = data.TryGetProperty("instructions", out var ins) ? ins.GetString() : "Short pins and connect USB.";

            // Render on Interactive BoardCanvas
            BoardCanvas.Children.Clear();

            string boardColor = "#1E3A2F";
            if (data.TryGetProperty("schematic", out var sch))
            {
                if (sch.TryGetProperty("board_color", out var bc)) boardColor = bc.GetString() ?? boardColor;
            }

            try
            {
                BoardCanvas.Background = new BrushConverter().ConvertFromString(boardColor) as Brush ?? Brushes.DarkSlateGray;
            }
            catch
            {
                BoardCanvas.Background = new SolidColorBrush(Color.FromRgb(30, 58, 47));
            }

            // Draw Motherboard Outline Frame
            var pcbBorder = new Rectangle
            {
                Width = 530,
                Height = 460,
                RadiusX = 16,
                RadiusY = 16,
                Stroke = new SolidColorBrush(Color.FromRgb(30, 70, 50)),
                StrokeThickness = 2,
                Fill = Brushes.Transparent
            };
            Canvas.SetLeft(pcbBorder, 10);
            Canvas.SetTop(pcbBorder, 10);
            BoardCanvas.Children.Add(pcbBorder);

            // Parse schematic coordinates
            if (sch.ValueKind == JsonValueKind.Object)
            {
                // CPU SoC
                DrawChip(sch, "cpu_pos", "CPU (SoC)", Color.FromRgb(30, 41, 59), Color.FromRgb(56, 189, 248));

                // eMMC / UFS Storage
                DrawChip(sch, "emmc_pos", "eMMC / UFS", Color.FromRgb(15, 23, 42), Color.FromRgb(129, 140, 248));

                // PMIC
                DrawChip(sch, "pmic_pos", "PMIC", Color.FromRgb(15, 23, 42), Color.FromRgb(100, 116, 139));

                // Battery Connector
                DrawComponent(sch, "battery_pos", "BATTERY FPC", Color.FromRgb(69, 10, 10), Color.FromRgb(248, 113, 113));

                // SIM Tray
                DrawComponent(sch, "sim_pos", "SIM TRAY", Color.FromRgb(51, 65, 85), Color.FromRgb(148, 163, 184));

                // Draw Testpoint Pads & Pins
                if (sch.TryGetProperty("tp_pads", out var pads) && pads.ValueKind == JsonValueKind.Array)
                {
                    var padPoints = new List<Point>();
                    foreach (var pad in pads.EnumerateArray())
                    {
                        string pName = pad.TryGetProperty("name", out var pn) ? pn.GetString() ?? "TP" : "TP";
                        string pColor = pad.TryGetProperty("color", out var pc) ? pc.GetString() ?? "#EF4444" : "#EF4444";
                        bool isSignal = pad.TryGetProperty("is_signal", out var sig) && sig.GetBoolean();

                        if (pad.TryGetProperty("pos", out var pos) && pos.ValueKind == JsonValueKind.Array)
                        {
                            double px = pos[0].GetDouble();
                            double py = pos[1].GetDouble();
                            padPoints.Add(new Point(px, py));

                            DrawTestPad(px, py, pName, pColor, isSignal);
                        }
                    }

                    // If 2 pads (signal & ground), draw connection tweezers guide line
                    if (padPoints.Count >= 2)
                    {
                        var guideLine = new Line
                        {
                            X1 = padPoints[0].X,
                            Y1 = padPoints[0].Y,
                            X2 = padPoints[1].X,
                            Y2 = padPoints[1].Y,
                            Stroke = new SolidColorBrush(Color.FromRgb(245, 158, 11)),
                            StrokeThickness = 2,
                            StrokeDashArray = new DoubleCollection { 4, 3 }
                        };
                        BoardCanvas.Children.Add(guideLine);

                        // Center indicator text: "Short with Tweezers"
                        double midX = (padPoints[0].X + padPoints[1].X) / 2.0;
                        double midY = (padPoints[0].Y + padPoints[1].Y) / 2.0;
                        var tweezersBadge = new Border
                        {
                            Background = new SolidColorBrush(Color.FromArgb(220, 15, 23, 42)),
                            BorderBrush = new SolidColorBrush(Color.FromRgb(245, 158, 11)),
                            BorderThickness = new Thickness(1),
                            CornerRadius = new CornerRadius(4),
                            Padding = new Thickness(6, 2, 6, 2)
                        };
                        tweezersBadge.Child = new TextBlock
                        {
                            Text = "⚡ Short Here",
                            FontSize = 9.5,
                            FontWeight = FontWeights.Bold,
                            Foreground = new SolidColorBrush(Color.FromRgb(251, 191, 36))
                        };
                        Canvas.SetLeft(tweezersBadge, midX - 35);
                        Canvas.SetTop(tweezersBadge, midY - 22);
                        BoardCanvas.Children.Add(tweezersBadge);
                    }
                }
            }
        }

        private void DrawChip(JsonElement sch, string propName, string label, Color bg, Color border)
        {
            if (sch.TryGetProperty(propName, out var pos) && pos.ValueKind == JsonValueKind.Array && pos.GetArrayLength() >= 4)
            {
                double x = pos[0].GetDouble();
                double y = pos[1].GetDouble();
                double w = pos[2].GetDouble();
                double h = pos[3].GetDouble();

                var borderRect = new Border
                {
                    Width = w,
                    Height = h,
                    Background = new SolidColorBrush(bg),
                    BorderBrush = new SolidColorBrush(border),
                    BorderThickness = new Thickness(1.5),
                    CornerRadius = new CornerRadius(4)
                };

                var tb = new TextBlock
                {
                    Text = label,
                    FontSize = 9,
                    FontWeight = FontWeights.Bold,
                    Foreground = new SolidColorBrush(border),
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center
                };
                borderRect.Child = tb;

                Canvas.SetLeft(borderRect, x);
                Canvas.SetTop(borderRect, y);
                BoardCanvas.Children.Add(borderRect);
            }
        }

        private void DrawComponent(JsonElement sch, string propName, string label, Color bg, Color border)
        {
            DrawChip(sch, propName, label, bg, border);
        }

        private void DrawTestPad(double x, double y, string name, string colorHex, bool isSignal)
        {
            Color c = Color.FromRgb(239, 68, 68);
            try
            {
                c = (Color)ColorConverter.ConvertFromString(colorHex);
            }
            catch { }

            // Glowing Outer Ring
            var glowRing = new Ellipse
            {
                Width = 24,
                Height = 24,
                Fill = new SolidColorBrush(Color.FromArgb(80, c.R, c.G, c.B)),
                Stroke = new SolidColorBrush(c),
                StrokeThickness = 1.5
            };
            Canvas.SetLeft(glowRing, x - 12);
            Canvas.SetTop(glowRing, y - 12);
            BoardCanvas.Children.Add(glowRing);

            // Core Metallic Contact Pad
            var corePad = new Ellipse
            {
                Width = 10,
                Height = 10,
                Fill = new SolidColorBrush(Color.FromRgb(254, 240, 138)), // Gold copper contact
                Stroke = new SolidColorBrush(c),
                StrokeThickness = 1.5
            };
            Canvas.SetLeft(corePad, x - 5);
            Canvas.SetTop(corePad, y - 5);
            BoardCanvas.Children.Add(corePad);

            // Text Label Box
            var labelBorder = new Border
            {
                Background = new SolidColorBrush(Color.FromArgb(220, 15, 23, 42)),
                BorderBrush = new SolidColorBrush(c),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(3),
                Padding = new Thickness(4, 1, 4, 1)
            };
            labelBorder.Child = new TextBlock
            {
                Text = name,
                FontSize = 9,
                FontWeight = FontWeights.Bold,
                Foreground = new SolidColorBrush(c)
            };
            Canvas.SetLeft(labelBorder, x + 14);
            Canvas.SetTop(labelBorder, y - 9);
            BoardCanvas.Children.Add(labelBorder);
        }

        private void OnZoomInClicked(object sender, RoutedEventArgs e)
        {
            _zoomFactor = Math.Min(2.5, _zoomFactor + 0.2);
            ApplyCanvasScale();
        }

        private void OnZoomOutClicked(object sender, RoutedEventArgs e)
        {
            _zoomFactor = Math.Max(0.5, _zoomFactor - 0.2);
            ApplyCanvasScale();
        }

        private void OnResetZoomClicked(object sender, RoutedEventArgs e)
        {
            _zoomFactor = 1.0;
            ApplyCanvasScale();
        }

        private void ApplyCanvasScale()
        {
            BoardCanvas.LayoutTransform = new ScaleTransform(_zoomFactor, _zoomFactor);
        }

        private void OnCopyInstructionsClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                string text = $"{TxtDetailModelName.Text} ({TxtDetailChipset.Text})\nMode: {TxtDetailMode.Text}\n\nProcedure:\n{TxtDetailInstructions.Text}";
                Clipboard.SetText(text);
                MessageBox.Show("Pinout procedure copied to clipboard!", "Copied", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch { }
        }
    }
}
