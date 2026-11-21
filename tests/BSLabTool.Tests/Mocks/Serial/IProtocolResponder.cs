using System;

namespace BSLabTool.Tests.Mocks.Serial
{
    public interface IProtocolResponder
    {
        /// <summary>
        /// Process bytes written by the host and return response bytes to be queued into RxBuffer.
        /// </summary>
        byte[] ProcessHostBytes(byte[] buffer, int offset, int count);

        /// <summary>
        /// Resets the internal state machine.
        /// </summary>
        void Reset();
    }
}
