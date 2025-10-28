import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('video') as File;

    if (!file) {
      return NextResponse.json({ error: 'No file uploaded' }, { status: 400 });
    }

    console.log(`[Upload] Received file: ${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`);

    // Forward the file to Python backend
    console.log(`[Upload] Forwarding to backend: ${BACKEND_URL}/api/analyze`);

    const backendFormData = new FormData();
    backendFormData.append('video', file);

    try {
      const backendResponse = await fetch(`${BACKEND_URL}/api/analyze`, {
        method: 'POST',
        body: backendFormData,
      });

      if (!backendResponse.ok) {
        const errorText = await backendResponse.text();
        console.error('[Upload] Backend error:', errorText);
        throw new Error(`Backend returned ${backendResponse.status}: ${errorText}`);
      }

      const analysisData = await backendResponse.json();
      console.log('[Upload] Analysis started:', analysisData.analysis_id);

      return NextResponse.json({
        id: analysisData.analysis_id,
        status: analysisData.status,
        message: 'Analysis started',
      });

    } catch (backendError) {
      console.error('[Upload] Failed to connect to backend:', backendError);

      // Check if backend is running
      if (backendError instanceof TypeError && backendError.message.includes('fetch')) {
        return NextResponse.json({
          error: 'Backend server is not running',
          details: `Please start the Python backend at ${BACKEND_URL}`,
          howToFix: 'Run: cd backend && source venv/bin/activate && python main.py',
        }, { status: 503 });
      }

      throw backendError;
    }

  } catch (error) {
    console.error('[Upload] Error:', error);
    return NextResponse.json(
      {
        error: 'Failed to process video',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
