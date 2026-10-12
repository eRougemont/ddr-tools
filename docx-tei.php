<?php declare(strict_types=1);

include_once(__DIR__ . '/vendor/autoload.php');

use Psr\Log\LogLevel;
use Oeuvres\Kit\{Cliglob, Filesys, Log};
use Oeuvres\Kit\Logger\{LoggerCli};
use Oeuvres\Teinte\Format\{Docx};



class Rougemont extends Cliglob
{
    /** Object to load Tei for exports */
    static $docx;

    public static function cli()
    {
        self::put('src_format', "docx");
        self::put('src_ext', ".docx");
        self::put('dst_format', "tei");
        self::put('dst_ext', ".xml");
        self::$docx = new Docx();
        Log::setLogger(new LoggerCli(LogLevel::DEBUG));
        // local xml template ?
        // self::$docx->user_template(__DIR__ . '/piaget_tmpl.xml');
        self::glob([__CLASS__, 'export']);
    }


    static function export($src_file, $dst_file)
    {
        Log::info($src_file . " > " . $dst_file);
        self::$docx->open($src_file);
        // self::$docx->teiURI($dst_file);
        // debug
        self::$docx->pkg();
        self::$docx->teilike();
        file_put_contents($dst_file .'_teilike.xml', self::$docx->teiXML());
        self::$docx->pcre(); // apply regex, custom re may break XML
        file_put_contents($dst_file .'_pcre.xml', self::$docx->teiXML());
        self::$docx->tmpl();
        file_put_contents($dst_file, self::$docx->teiXML());
    }
}

if (Rougemont::isCli()) {
    Rougemont::cli();
}