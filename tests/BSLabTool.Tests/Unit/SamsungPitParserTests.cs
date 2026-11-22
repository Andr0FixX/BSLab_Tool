using System;
using Xunit;
using FluentAssertions;
using BSLabTool.UI.Services;

namespace BSLabTool.Tests.Unit
{
    public class SamsungPitParserTests
    {
        [Fact]
        public void Parse_TabA8_X200_ParsesModelAndRevCorrectly()
        {
            // Bug fix verification: Previously parsed as SM-X200X, Rev: S, Build: 3CWK
            string fn = "X200XXS3CWK1_PIT_001ca890.pit";
            var item = SamsungPitParser.Parse(fn);

            item.ModelCode.Should().Be("SM-X200");
            item.ModelName.Should().Contain("Galaxy Tab A8");
            item.VendorCode.Should().Be("XX");
            item.VendorRegion.Should().Contain("Global / Europe");
            item.BinaryRev.Should().Be("S3");
            item.BuildNumber.Should().Be("CWK1");
            item.PitHash.Should().Be("001ca890");
        }

        [Fact]
        public void Parse_TabA8_X200_CWG3_ParsesCorrectly()
        {
            string fn = "X200XXS3CWG3_PIT_215ee6e2.pit";
            var item = SamsungPitParser.Parse(fn);

            item.ModelCode.Should().Be("SM-X200");
            item.BinaryRev.Should().Be("S3");
            item.BuildNumber.Should().Be("CWG3");
        }

        [Fact]
        public void Parse_GalaxyA03_A035F_ParsesCorrectly()
        {
            string fn = "A035FXXU1AVD3_PIT_0662e1af.pit";
            var item = SamsungPitParser.Parse(fn);

            item.ModelCode.Should().Be("SM-A035F");
            item.ModelName.Should().Contain("Galaxy A03");
            item.BinaryRev.Should().Be("U1");
            item.BuildNumber.Should().Be("AVD3");
        }

        [Fact]
        public void Parse_GalaxyA01_Cricket_A015AZ_PreservesFullModel()
        {
            string fn = "A015AZTUU4BWA1_PIT_a015a.pit";
            var item = SamsungPitParser.Parse(fn);

            item.ModelCode.Should().Be("SM-A015AZ");
            item.VendorCode.Should().Be("TU");
            item.BinaryRev.Should().Be("U4");
            item.BuildNumber.Should().Be("BWA1");
        }

        [Fact]
        public void Parse_Note10Plus_USA_N975U1_PreservesFullModel()
        {
            string fn = "N975U1UES8HWG1_PIT_b82340c4.pit";
            var item = SamsungPitParser.Parse(fn);

            item.ModelCode.Should().Be("SM-N975U1");
            item.ModelName.Should().Contain("Galaxy Note 10+");
            item.BinaryRev.Should().Be("S8");
            item.BuildNumber.Should().Be("HWG1");
        }

        [Fact]
        public void Parse_GalaxyA22_5G_HexRevision_ParsesCorrectly()
        {
            // Rev B is binary 11
            string fn = "A226BXXSBDYA1_PIT_026dd21f.pit";
            var item = SamsungPitParser.Parse(fn);

            item.ModelCode.Should().Be("SM-A226B");
            item.ModelName.Should().Contain("Galaxy A22 5G");
            item.BinaryRev.Should().Be("SB");
            item.BuildNumber.Should().Be("DYA1");
        }

        [Fact]
        public void Parse_TabA8_T290_ParsesCorrectly()
        {
            string fn = "T290XXS4CWA1_PIT_abfe49a3.pit";
            var item = SamsungPitParser.Parse(fn);

            item.ModelCode.Should().Be("SM-T290");
            item.ModelName.Should().Contain("Galaxy Tab A 8.0");
            item.BinaryRev.Should().Be("S4");
            item.BuildNumber.Should().Be("CWA1");
        }

        [Fact]
        public void Parse_SAMDev_TestPit_ParsesCorrectly()
        {
            string fn = "SAMDev_PIT_189613c6.pit";
            var item = SamsungPitParser.Parse(fn);

            item.ModelCode.Should().Be("SAM-DEV");
            item.ModelName.Should().Contain("Samsung Engineering Test Board");
            item.BinaryRev.Should().Be("Test");
        }

        [Fact]
        public void Parse_UniversalPit_ParsesCorrectly()
        {
            string fn = "_PIT_15c0355f.pit";
            var item = SamsungPitParser.Parse(fn);

            item.ModelCode.Should().Be("SM-UNIVERSAL");
            item.ModelName.Should().Contain("Universal Samsung Partition Map");
            item.BinaryRev.Should().Be("All");
        }
    }
}
