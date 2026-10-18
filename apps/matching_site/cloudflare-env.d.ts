declare namespace Cloudflare {
  interface Env {
    DB?: D1Database;
    BUCKET?: R2Bucket;
    SLOWMATCH_TEST_SCOPES?: string;
    SLOWMATCH_DEFAULT_TEST_SCOPE?: string;
  }
}
