using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;

namespace BSLabTool.UI.Views
{
    /// <summary>
    /// Interaction logic for WorkshopPosBillingWindow.xaml
    /// Workshop POS, Repair Job Ticket & Customer Invoice Generator.
    /// Provides thermal printer (80mm) receipt generation, WhatsApp notification, and local JSON database storage.
    /// </summary>
    public partial class WorkshopPosBillingWindow : Window
    {
        private int _currentTicketNumber = 1049;
        private readonly string _ticketsDir = @"C:\BSLab_Tool\WorkshopTickets";
        private readonly string _ticketsFilePath = @"C:\BSLab_Tool\WorkshopTickets\tickets.json";

        public WorkshopPosBillingWindow()
        {
            InitializeComponent();
            EnsureStorageDir();
            UpdateReceiptPreview();
        }

        private void EnsureStorageDir()
        {
            try
            {
                if (!Directory.Exists(_ticketsDir))
                {
                    Directory.CreateDirectory(_ticketsDir);
                }
            }
            catch { }
        }

        private void OnHeaderMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ButtonState == MouseButtonState.Pressed)
            {
                DragMove();
            }
        }

        private void OnCloseClicked(object sender, RoutedEventArgs e)
        {
            Close();
        }

        private void OnFormInputChanged(object sender, TextChangedEventArgs e)
        {
            CalculateBalance();
            UpdateReceiptPreview();
        }

        private void OnStatusChanged(object sender, SelectionChangedEventArgs e)
        {
            UpdateReceiptPreview();
        }

        private void CalculateBalance()
        {
            if (TxtTotalCost == null || TxtAdvancePaid == null || TxtBalanceDue == null) return;

            decimal total = 0;
            decimal advance = 0;
            decimal.TryParse(TxtTotalCost.Text, out total);
            decimal.TryParse(TxtAdvancePaid.Text, out advance);

            decimal balance = Math.Max(0, total - advance);
            TxtBalanceDue.Text = balance.ToString("F0");
        }

        private void UpdateReceiptPreview()
        {
            if (TxtThermalReceipt == null) return;

            string ticketId = $"BS-2026-{_currentTicketNumber}";
            TxtTicketPill.Text = ticketId;

            string shopName = TxtShopName?.Text ?? "BS LAB GSM CARE";
            string shopPhone = TxtShopPhone?.Text ?? "";
            string shopAddress = TxtShopAddress?.Text ?? "";
            string customerName = TxtCustomerName?.Text ?? "Customer";
            string customerPhone = TxtCustomerPhone?.Text ?? "";
            string deviceModel = TxtDeviceModel?.Text ?? "Mobile Device";
            string deviceImei = TxtDeviceImei?.Text ?? "N/A";
            string fault = TxtFaultDescription?.Text ?? "Hardware / Software Repair";
            string condition = TxtCondition?.Text ?? "Good";
            string status = (CmbJobStatus?.SelectedItem as ComboBoxItem)?.Content.ToString() ?? "RECEIVED";
            string total = TxtTotalCost?.Text ?? "0";
            string advance = TxtAdvancePaid?.Text ?? "0";
            string balance = TxtBalanceDue?.Text ?? "0";

            var sb = new StringBuilder();
            sb.AppendLine("================================");
            sb.AppendLine(CenterText(shopName, 32));
            sb.AppendLine(CenterText(shopAddress, 32));
            sb.AppendLine(CenterText($"TEL: {shopPhone}", 32));
            sb.AppendLine("================================");
            sb.AppendLine(CenterText("REPAIR JOB TICKET / INVOICE", 32));
            sb.AppendLine($"TICKET #: {ticketId}");
            sb.AppendLine($"DATE    : {DateTime.Now:yyyy-MM-dd  HH:mm}");
            sb.AppendLine("--------------------------------");
            sb.AppendLine($"CUSTOMER: {customerName}");
            sb.AppendLine($"CONTACT : {customerPhone}");
            sb.AppendLine($"DEVICE  : {deviceModel}");
            sb.AppendLine($"IMEI/SN : {deviceImei}");
            sb.AppendLine("--------------------------------");
            sb.AppendLine($"JOB FAULT:");
            sb.AppendLine($"  {WrapText(fault, 30)}");
            sb.AppendLine($"CONDITION:");
            sb.AppendLine($"  {WrapText(condition, 30)}");
            sb.AppendLine($"STATUS  : {status}");
            sb.AppendLine("================================");
            sb.AppendLine($"TOTAL AMOUNT : Rs {total,10}");
            sb.AppendLine($"ADVANCE PAID : Rs {advance,10}");
            sb.AppendLine($"BALANCE DUE  : Rs {balance,10}");
            sb.AppendLine("================================");
            sb.AppendLine(CenterText("* BARCODE / TRACKING *", 32));
            sb.AppendLine(CenterText("||| || |||| | ||| |||| || |", 32));
            sb.AppendLine(CenterText($"*{ticketId}*", 32));
            sb.AppendLine("================================");
            sb.AppendLine(CenterText("TERMS & CONDITIONS", 32));
            sb.AppendLine("• Handset check mandatory upon pickup");
            sb.AppendLine("• No warranty on Dead/Water damage");
            sb.AppendLine("• Keep receipt safe for pickup");
            sb.AppendLine(CenterText("Powered by BS LAB TOOL™ PRO", 32));
            sb.AppendLine("================================");

            TxtThermalReceipt.Text = sb.ToString();
        }

        private string CenterText(string text, int width)
        {
            if (string.IsNullOrEmpty(text)) return string.Empty;
            if (text.Length >= width) return text.Substring(0, width);
            int leftPad = (width - text.Length) / 2;
            return new string(' ', leftPad) + text;
        }

        private string WrapText(string text, int width)
        {
            if (string.IsNullOrEmpty(text)) return string.Empty;
            if (text.Length <= width) return text;
            return text.Substring(0, width) + Environment.NewLine + "  " + text.Substring(width);
        }

        private void OnPrintThermalClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                var printDlg = new PrintDialog();
                if (printDlg.ShowDialog() == true)
                {
                    var doc = new FlowDocument();
                    var p = new Paragraph(new Run(TxtThermalReceipt.Text))
                    {
                        FontFamily = new FontFamily("Courier New"),
                        FontSize = 10,
                        Margin = new Thickness(0)
                    };
                    doc.Blocks.Add(p);
                    doc.PageWidth = 280; // 80mm equivalent
                    doc.PagePadding = new Thickness(5);

                    var paginator = ((IDocumentPaginatorSource)doc).DocumentPaginator;
                    printDlg.PrintDocument(paginator, $"BSLab_Ticket_{TxtTicketPill.Text}");

                    MessageBox.Show("Thermal Ticket Sent to Printer Successfully!", "Print Job", MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Print Error: {ex.Message}\n(Make sure a printer is configured in Windows)", "Printer Error", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        private void OnSendWhatsAppClicked(object sender, RoutedEventArgs e)
        {
            string phone = TxtCustomerPhone.Text.Trim().Replace("+", "").Replace(" ", "").Replace("-", "");
            if (string.IsNullOrEmpty(phone))
            {
                MessageBox.Show("Please enter a valid Customer WhatsApp number first.", "WhatsApp Dispatcher", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            string ticketId = TxtTicketPill.Text;
            string customer = TxtCustomerName.Text;
            string device = TxtDeviceModel.Text;
            string balance = TxtBalanceDue.Text;
            string status = (CmbJobStatus.SelectedItem as ComboBoxItem)?.Content.ToString() ?? "RECEIVED";

            string msg = $"السلام علیکم {customer} صاحب!%0A" +
                         $"آپ کا فون *{device}* ہمارے سروس سینٹر پر موصول ہو چکا ہے۔%0A" +
                         $"🎫 *ٹکٹ نمبر:* {ticketId}%0A" +
                         $"📋 *حیثیت:* {status}%0A" +
                         $"💰 *بقایا رقم:* Rs. {balance}%0A%0A" +
                         $"شکریہ: *{TxtShopName.Text}*%0A" +
                         $"📞 رابطہ: {TxtShopPhone.Text}";

            string url = $"https://wa.me/{phone}?text={msg}";

            try
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = url,
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Could not open WhatsApp: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void OnSaveTicketClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                EnsureStorageDir();

                var ticketData = new
                {
                    TicketId = TxtTicketPill.Text,
                    CreatedAt = DateTime.UtcNow,
                    ShopName = TxtShopName.Text,
                    CustomerName = TxtCustomerName.Text,
                    CustomerPhone = TxtCustomerPhone.Text,
                    DeviceModel = TxtDeviceModel.Text,
                    Imei = TxtDeviceImei.Text,
                    Fault = TxtFaultDescription.Text,
                    Condition = TxtCondition.Text,
                    TotalCost = TxtTotalCost.Text,
                    AdvancePaid = TxtAdvancePaid.Text,
                    BalanceDue = TxtBalanceDue.Text,
                    Status = (CmbJobStatus.SelectedItem as ComboBoxItem)?.Content.ToString()
                };

                string jsonLine = JsonSerializer.Serialize(ticketData) + Environment.NewLine;
                File.AppendAllText(_ticketsFilePath, jsonLine);

                MessageBox.Show($"Ticket {TxtTicketPill.Text} Saved Successfully to Database!\nSaved to: {_ticketsFilePath}",
                    "Ticket Saved", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error saving ticket: {ex.Message}", "Database Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void OnNewTicketClicked(object sender, RoutedEventArgs e)
        {
            _currentTicketNumber++;
            TxtTicketPill.Text = $"BS-2026-{_currentTicketNumber}";
            TxtCustomerName.Text = "";
            TxtCustomerPhone.Text = "";
            TxtDeviceModel.Text = "";
            TxtDeviceImei.Text = "";
            TxtFaultDescription.Text = "";
            TxtTotalCost.Text = "0";
            TxtAdvancePaid.Text = "0";
            TxtBalanceDue.Text = "0";
            CmbJobStatus.SelectedIndex = 0;
            UpdateReceiptPreview();
        }
    }
}
