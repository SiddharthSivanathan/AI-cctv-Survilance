import { NextResponse } from 'next/server';

/** Liveness probe for the web app (used by Docker/K8s healthchecks). */
export function GET() {
  return NextResponse.json({
    status: 'ok',
    service: 'web',
    version: process.env.npm_package_version ?? '0.1.0',
  });
}
